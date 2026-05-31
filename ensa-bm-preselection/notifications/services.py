# notifications/services.py
# Service d'envoi de notifications emails avec support WebSocket temps réel

import uuid
import threading
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


TEMPLATES_SUJET = {
    'SOUMISSION':   "✅ Votre dossier a été soumis avec succès",
    'REJET_AUTO':   "❌ Votre dossier n'est pas éligible",
    'REJET_MANUEL': "❌ Votre candidature n'a pas été retenue",
    'PRESELECTION': "🎉 Félicitations — Vous êtes présélectionné(e) !",
    'INCOMPLET':    "⚠️ Votre dossier est incomplet",
    'COMPLEMENT':   "📎 Complément de document demandé",
    'ADMIS_FINAL':  "🎓 Félicitations — Vous êtes admis(e) à l'ENSA BM",
    'RECALE_FINAL': "Résultats épreuve écrite — ENSA Béni Mellal",
}


import logging
import traceback
logger = logging.getLogger(__name__)


def envoyer_notification(dossier, type_notif, raise_exception=False):
    """Envoie une notification email individuelle pour un dossier."""
    sujet = TEMPLATES_SUJET.get(type_notif, "Mise à jour de votre dossier")
    contenu = _generer_contenu(dossier, type_notif)

    notif = Notification.objects.create(
        destinataire=dossier.candidat.user,
        type_notif=type_notif,
        sujet=sujet,
        contenu_html=contenu,
    )

    try:
        msg = EmailMultiAlternatives(
            subject=sujet,
            body=contenu,
            from_email=None,  # Utilise DEFAULT_FROM_EMAIL de settings
            to=[dossier.candidat.user.email]
        )
        msg.attach_alternative(contenu, "text/html")
        msg.send()
        notif.statut = Notification.Statut.ENVOYEE
        notif.envoyee_le = timezone.now()
        logger.info(f"Email envoyé à {dossier.candidat.user.email}")
    except Exception as e:
        notif.statut = Notification.Statut.ECHEC
        notif.erreur = f"{type(e).__name__}: {str(e)}"
        logger.error(
            f"Échec email pour {dossier.candidat.user.email}: "
            f"{traceback.format_exc()}"
        )
        if raise_exception:
            raise e
    finally:
        notif.save()


# ── Envoi en masse avec progression WebSocket ─────────────────────


def demarrer_notification_masse(filiere_id=None, envoye_par=None):
    """
    Démarre l'envoi en arrière-plan et retourne le task_id.
    Appelée par la vue HTTP — retour immédiat.
    """
    task_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=envoyer_notification_masse_async,
        args=(task_id, filiere_id, envoye_par),
        daemon=True
    )
    thread.start()

    return task_id


def envoyer_notification_masse_async(task_id, filiere_id=None, envoye_par=None):
    """
    Exécuté dans un thread séparé.
    Envoie les emails et publie la progression via WebSocket.
    """
    channel_layer = get_channel_layer()
    group_name = f'notif_task_{task_id}'

    # Récupérer les dossiers à notifier
    dossiers = _get_dossiers_a_notifier(filiere_id)
    total = len(dossiers)
    envoyes = echecs = ignores = 0
    details_echecs = []

    for index, dossier in enumerate(dossiers, 1):
        candidat_nom = dossier.candidat.nom_complet
        email = dossier.candidat.user.email

        # Vérifier doublon (déjà notifié dans les 24h)
        if _deja_notifie_recemment(dossier):
            ignores += 1
            statut = 'IGNORE'
            erreur = ''
        else:
            # Tenter l'envoi
            try:
                envoyer_notification(dossier, 'PRESELECTION', raise_exception=True)
                envoyes += 1
                statut = 'ENVOYE'
                erreur = ''
            except Exception as e:
                echecs += 1
                statut = 'ECHEC'
                erreur = f"{type(e).__name__}: {str(e)}"[0:100]
                details_echecs.append({
                    'candidat': candidat_nom,
                    'email': email,
                    'erreur': erreur
                })

        # Publier la progression via WebSocket
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification.progress',
                'current': index,
                'total': total,
                'candidat': candidat_nom,
                'email': email,
                'statut': statut,
                'erreur': erreur,
            }
        )

    # Publier le message de fin
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification.termine',
            'envoyes': envoyes,
            'echecs': echecs,
            'ignores': ignores,
            'total': total,
            'details_echecs': details_echecs,
        }
    )


def compter_a_notifier(filiere_id=None):
    """Retourne les statistiques des candidats à notifier."""
    dossiers = _get_dossiers_a_notifier(filiere_id)
    total = len(dossiers)
    deja_notifies = sum(1 for d in dossiers if _deja_notifie_recemment(d))
    return {
        'total': total,
        'a_notifier': total - deja_notifies,
        'deja_notifies': deja_notifies,
    }


def generer_apercu_email(filiere_id=None):
    """Génère un aperçu de l'email qui sera envoyé."""
    from candidatures.models import Dossier
    dossier_exemple = Dossier.objects.filter(
        statut='PRESELECTIONNE'
    ).select_related('candidat', 'candidat__user', 'filiere').first()

    if not dossier_exemple:
        return {
            'sujet': TEMPLATES_SUJET.get('PRESELECTION', ''),
            'apercu_html': '<p>Aucun dossier présélectionné pour générer un aperçu.</p>',
        }

    return {
        'sujet': TEMPLATES_SUJET.get('PRESELECTION', ''),
        'apercu_html': _generer_contenu(dossier_exemple, 'PRESELECTION'),
    }


# ── Helpers internes ──────────────────────────────────────────────


def _get_dossiers_a_notifier(filiere_id=None):
    from candidatures.models import Dossier
    qs = Dossier.objects.filter(
        statut='PRESELECTIONNE'
    ).select_related('candidat', 'candidat__user', 'filiere')
    if filiere_id:
        qs = qs.filter(filiere_id=filiere_id)
    return list(qs)


def _deja_notifie_recemment(dossier):
    from datetime import timedelta
    return Notification.objects.filter(
        destinataire=dossier.candidat.user,
        type_notif='PRESELECTION',
        statut='ENVOYEE',
        envoyee_le__gte=timezone.now() - timedelta(hours=24)
    ).exists()


def _generer_corps_admis_final(dossier, filiere):
    """Génère le corps HTML pour un candidat admis à l'épreuve écrite."""
    note_ecrite = getattr(dossier, 'notes_ecrits', None)
    note_obj = note_ecrite.first() if note_ecrite else None
    note_val = float(note_obj.note) if note_obj and note_obj.note else '—'
    note_sur = float(note_obj.epreuve.note_sur) if note_obj else 20
    rang = dossier.rang_final if dossier.rang_final else '—'
    score_final = float(dossier.score_final) if dossier.score_final else '—'

    # Infos oral
    epreuve = note_obj.epreuve if note_obj else None
    date_oral = epreuve.date_oral if epreuve and epreuve.date_oral else None
    lieu_oral = epreuve.lieu_oral if epreuve and epreuve.lieu_oral else 'ENSA Béni Mellal'
    heure_oral = epreuve.heure_oral if epreuve and epreuve.heure_oral else '09:00'

    if date_oral:
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        mois_noms = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                     'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
        date_oral_str = f"{jours[date_oral.weekday()]} {date_oral.day} {mois_noms[date_oral.month - 1]} {date_oral.year}"
    else:
        date_oral_str = 'Date à confirmer prochainement'

    return f"""
    <p>Nous avons l'honneur de vous informer que vous avez été
    <strong>admis(e)</strong> à l'épreuve écrite d'accès à l'ENSA Béni Mellal.</p>

    <div style="background:#E8F8F0; border-left:4px solid #27AE60;
                padding:16px; margin:16px 0; border-radius:4px">
      <h3 style="margin:0 0 10px 0; color:#27AE60">📊 Résultats Épreuve Écrite</h3>
      <table style="width:100%; border-collapse:collapse">
        <tr><td style="padding:6px 0"><strong>Filière</strong></td>
            <td>{filiere.nom}</td></tr>
        <tr><td style="padding:6px 0"><strong>Note épreuve</strong></td>
            <td>{note_val}/{note_sur}</td></tr>
        <tr><td style="padding:6px 0"><strong>Rang final</strong></td>
            <td>{rang}ème</td></tr>
        <tr><td style="padding:6px 0"><strong>Score global</strong></td>
            <td>{score_final}/20</td></tr>
      </table>
    </div>

    <div style="background:#EFF6FF; border-left:4px solid #3B82F6;
                padding:16px; margin:16px 0; border-radius:4px">
      <h3 style="margin:0 0 10px 0; color:#1B3A6B">📋 Convocation — Épreuve Orale</h3>
      <table style="width:100%; border-collapse:collapse">
        <tr><td style="padding:8px 0; font-size:15px"><strong>📅 Date :</strong></td>
            <td style="padding:8px 0; font-size:15px; color:#1B3A6B"><strong>{date_oral_str}</strong></td></tr>
        <tr><td style="padding:8px 0; font-size:15px"><strong>⏰ Heure :</strong></td>
            <td style="padding:8px 0; font-size:15px; color:#1B3A6B"><strong>{heure_oral}</strong></td></tr>
        <tr><td style="padding:8px 0; font-size:15px"><strong>📍 Lieu :</strong></td>
            <td style="padding:8px 0; font-size:15px; color:#1B3A6B"><strong>{lieu_oral}</strong></td></tr>
      </table>
    </div>

    <p style="color:#DC2626; font-weight:bold; text-align:center; margin:16px 0">
      ⚠️ Toute absence non justifiée sera considérée comme un désistement définitif.
    </p>

    <p><strong>Documents à présenter :</strong></p>
    <ul style="color:#374151">
      <li>Convocation imprimée (téléchargeable depuis votre espace candidat)</li>
      <li>Carte d'identité nationale (CIN) originale</li>
      <li>Copie certifiée conforme du baccalauréat</li>
    </ul>

    <p style="background:#F0FDF4; padding:12px; border-radius:6px; text-align:center">
      📥 <strong>Téléchargez votre convocation</strong> depuis votre espace candidat
      → Rubrique « Résultats Épreuve Écrite »
    </p>
    """


def _generer_corps_recale_final(dossier, filiere):
    """Génère le corps HTML pour un candidat recalé à l'épreuve écrite."""
    note_ecrite = getattr(dossier, 'notes_ecrits', None)
    note_obj = note_ecrite.first() if note_ecrite else None
    note_val = float(note_obj.note) if note_obj and note_obj.note else '—'
    note_sur = float(note_obj.epreuve.note_sur) if note_obj else 20
    seuil = float(note_obj.epreuve.seuil_admission) if note_obj else '—'

    return f"""
    <p>Nous avons le regret de vous informer que votre résultat à l'épreuve
    écrite ne vous permet pas d'accéder au cycle {filiere.get_niveau_display()}
    cette année.</p>

    <div style="background:#FDF0F0; border-left:4px solid #C0392B;
                padding:16px; margin:16px 0; border-radius:4px">
      <table style="width:100%; border-collapse:collapse">
        <tr><td style="padding:6px 0"><strong>Note obtenue</strong></td>
            <td>{note_val}/{note_sur}</td></tr>
        <tr><td style="padding:6px 0"><strong>Seuil requis</strong></td>
            <td>{seuil}/{note_sur}</td></tr>
      </table>
    </div>

    <p>Nous vous encourageons à tenter à nouveau votre chance
    lors de la prochaine session. L'ENSA Béni Mellal vous souhaite
    bonne continuation dans vos études.</p>
    """


def _generer_contenu(dossier, type_notif):
    candidat = dossier.candidat
    filiere = dossier.filiere

    base = f"""
    <div style="font-family:Arial,sans-serif; max-width:600px; margin:auto">
      <div style="background:#1B3A6B; color:white; padding:20px; text-align:center">
        <h2>ENSA Béni Mellal — Présélection {filiere.niveau}</h2>
      </div>
      <div style="padding:24px">
        <p>Bonjour <strong>{candidat.nom_complet}</strong>,</p>
    """

    corps = {
        'SOUMISSION':   f"<p>Votre dossier pour la filière <strong>{filiere.nom}</strong> a bien été reçu et est en cours d'examen.</p>",
        'REJET_AUTO':   f"<p>Après analyse automatique, votre dossier ne répond pas aux critères d'éligibilité.</p><p><strong>Motif :</strong> {dossier.motif_rejet}</p>",
        'REJET_MANUEL': "<p>Après examen de votre dossier, votre candidature n'a pas été retenue.</p>",
        'PRESELECTION': f"<p>Nous avons le plaisir de vous informer que vous êtes <strong>présélectionné(e)</strong> pour la filière <strong>{filiere.nom}</strong>.</p><p>Score obtenu : <strong>{dossier.score}/20</strong></p>",
        'INCOMPLET':    "<p>Votre dossier est incomplet. Veuillez vous connecter pour compléter les documents manquants.</p>",
        'ADMIS_FINAL':  _generer_corps_admis_final(dossier, filiere),
        'RECALE_FINAL': _generer_corps_recale_final(dossier, filiere),
    }

    fin = """
        <p style="color:#666; font-size:12px; margin-top:32px">
          ENSA Béni Mellal — Service Scolarité
        </p>
      </div>
    </div>
    """
    return base + corps.get(type_notif, '') + fin