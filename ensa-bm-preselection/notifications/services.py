# notifications/services.py

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from .models import Notification


TEMPLATES_SUJET = {
    'SOUMISSION':   "✅ Votre dossier a été soumis avec succès",
    'REJET_AUTO':   "❌ Votre dossier n'est pas éligible",
    'REJET_MANUEL': "❌ Votre candidature n'a pas été retenue",
    'PRESELECTION': "🎉 Félicitations — Vous êtes présélectionné(e) !",
    'INCOMPLET':    "⚠️ Votre dossier est incomplet",
    'COMPLEMENT':   "📎 Complément de document demandé",
}


def envoyer_notification(dossier, type_notif):
    sujet  = TEMPLATES_SUJET.get(type_notif, "Mise à jour de votre dossier")
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
        notif.statut    = Notification.Statut.ENVOYEE
        notif.envoyee_le = timezone.now()
    except Exception as e:
        notif.statut = Notification.Statut.ECHEC
        notif.erreur = str(e)
    finally:
        notif.save()


def _generer_contenu(dossier, type_notif):
    candidat = dossier.candidat
    filiere  = dossier.filiere

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
        'REJET_MANUEL': f"<p>Après examen de votre dossier, votre candidature n'a pas été retenue.</p>",
        'PRESELECTION': f"<p>Nous avons le plaisir de vous informer que vous êtes <strong>présélectionné(e)</strong> pour la filière <strong>{filiere.nom}</strong>.</p><p>Score obtenu : <strong>{dossier.score}/20</strong></p>",
        'INCOMPLET':    f"<p>Votre dossier est incomplet. Veuillez vous connecter pour compléter les documents manquants.</p>",
    }

    fin = """
        <p style="color:#666; font-size:12px; margin-top:32px">
          ENSA Béni Mellal — Service Scolarité
        </p>
      </div>
    </div>
    """
    return base + corps.get(type_notif, '') + fin