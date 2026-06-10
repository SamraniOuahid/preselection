# administration/services/import_excel_oral.py
"""
Service d'importation Excel/CSV pour les admis à l'épreuve orale.

Colonnes acceptées (insensible à la casse, espaces ignorés) :
    cne | code_massar | id

Logique :
    - Parse le fichier (openpyxl pour xlsx/xls, csv stdlib pour csv)
    - Pour chaque identifiant trouvé, cherche le Dossier correspondant
      dans la filière de l'épreuve orale (statut ADMIS_FINAL ou déjà CONVOQUE_ORAL)
    - Crée une ConvocationOrale avec horaire calculé depuis filiere.date_oral
    - Génère le PDF de convocation et envoie l'email
    - Collecte les erreurs ligne par ligne sans interrompre l'import

Atomicité :
    - Tout est enveloppé dans transaction.atomic().
    - Une ValidationError préliminaire (colonnes manquantes, fichier vide)
      annule tout avant d'écrire quoi que ce soit.
"""

import csv
import datetime
import io
import logging

import openpyxl
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from administration.models import ConvocationOrale, EpreuveOrale
from administration.services.generation_pdf import generer_convocation_pdf
from candidatures.models import Dossier
from notifications.services import envoyer_notification

logger = logging.getLogger(__name__)

# Colonnes valides (toutes normalisées en minuscule sans espaces)
_COLONNES_VALIDES = {'cne', 'code_massar', 'id'}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de parsing
# ─────────────────────────────────────────────────────────────────────────────

def _detecter_colonne_sans_erreur(headers: list[str]) -> str | None:
    """Renvoie la première colonne valide trouvée, ou None."""
    for col in ('cne', 'code_massar', 'id'):
        if col in headers:
            return col
    return None


def _lire_lignes_xlsx(fichier) -> tuple[str, list[dict]]:
    """
    Lit un fichier xlsx/xls. Retourne (colonne_cle, liste_de_dicts).
    Recherche la ligne d'en-tête contenant 'cne', 'code_massar' ou 'id'.
    """
    try:
        wb = openpyxl.load_workbook(fichier, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as exc:
        raise ValidationError(f"Fichier Excel illisible ou corrompu : {exc}")

    if not rows:
        raise ValidationError("Le fichier est vide.")

    # Trouver la ligne contenant l'en-tête
    header_row_idx = -1
    colonne = None
    headers = []

    for idx, row in enumerate(rows):
        if not row or not any(cell is not None and str(cell).strip() for cell in row):
            continue
        row_headers = [str(h).strip().lower() if h is not None else '' for h in row]
        col = _detecter_colonne_sans_erreur(row_headers)
        if col:
            header_row_idx = idx
            colonne = col
            headers = row_headers
            break

    if header_row_idx == -1:
        # Aucun en-tête valide n'a été trouvé. On lève l'erreur avec les colonnes de la première ligne non-vide.
        first_non_empty_row = next((r for r in rows if r and any(cell is not None and str(cell).strip() for cell in r)), rows[0])
        first_headers = [str(h).strip().lower() if h is not None else '' for h in first_non_empty_row]
        _detecter_colonne(first_headers)

    idx = headers.index(colonne)
    lignes = []
    for row in rows[header_row_idx + 1:]:
        if idx < len(row):
            val = row[idx]
            if val is not None and str(val).strip():
                lignes.append({colonne: str(val).strip()})

    return colonne, lignes


def _lire_lignes_csv(fichier) -> tuple[str, list[dict]]:
    """
    Lit un fichier CSV (UTF-8 ou latin-1).
    Recherche la ligne d'en-tête contenant 'cne', 'code_massar' ou 'id'.
    """
    contenu_bytes = fichier.read()
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            contenu = contenu_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValidationError("Encodage du fichier CSV non reconnu (essayez UTF-8 ou latin-1).")

    try:
        reader = csv.reader(io.StringIO(contenu))
        rows = list(reader)
    except Exception as exc:
        raise ValidationError(f"CSV illisible : {exc}")

    if not rows:
        raise ValidationError("Le fichier est vide.")

    # Trouver la ligne contenant l'en-tête
    header_row_idx = -1
    colonne = None
    headers = []

    for idx, row in enumerate(rows):
        if not row or not any(cell.strip() for cell in row):
            continue
        row_headers = [h.strip().lower() for h in row]
        col = _detecter_colonne_sans_erreur(row_headers)
        if col:
            header_row_idx = idx
            colonne = col
            headers = row_headers
            break

    if header_row_idx == -1:
        # Aucun en-tête valide n'a été trouvé. On lève l'erreur avec les colonnes de la première ligne non-vide.
        first_non_empty_row = next((r for r in rows if r and any(cell.strip() for cell in r)), rows[0])
        first_headers = [h.strip().lower() for h in first_non_empty_row]
        _detecter_colonne(first_headers)

    idx = headers.index(colonne)
    lignes = []
    for row in rows[header_row_idx + 1:]:
        if idx < len(row):
            val = row[idx]
            if val and val.strip():
                lignes.append({colonne: val.strip()})

    return colonne, lignes


def _detecter_colonne(headers: list[str]) -> str:
    """Renvoie la première colonne valide trouvée, ou lève ValidationError."""
    for col in ('cne', 'code_massar', 'id'):
        if col in headers:
            return col
    raise ValidationError(
        f"Colonnes obligatoires manquantes. Colonne attendue : 'cne', 'code_massar' ou 'id'. "
        f"Colonnes trouvées : {', '.join(headers) or '(aucune)'}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Calcul des horaires de passage
# ─────────────────────────────────────────────────────────────────────────────

def _heure_debut_from_filiere(filiere) -> datetime.time:
    """Extrait l'heure de début depuis filiere.date_oral (DateTimeField)."""
    if filiere.date_oral:
        tz = timezone.get_current_timezone()
        dt_local = filiere.date_oral.astimezone(tz)
        return dt_local.time().replace(second=0, microsecond=0)
    return datetime.time(9, 0)


def _calculer_heure_passage(heure_debut: datetime.time, rang: int, duree: int) -> datetime.time:
    delta = datetime.timedelta(minutes=rang * duree)
    base = datetime.datetime.combine(datetime.date.today(), heure_debut)
    return (base + delta).time()


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────────────────────────────────────

def importer_admis_oral_depuis_fichier(
    fichier,
    extension: str,
    epreuve: EpreuveOrale,
    acteur,
) -> dict:
    """
    Fonction principale appelée depuis la vue.

    Args:
        fichier  : InMemoryUploadedFile Django
        extension: 'xlsx' | 'xls' | 'csv'
        epreuve  : instance EpreuveOrale cible
        acteur   : utilisateur connecté (pour historique + décision)

    Returns:
        dict avec les clés : traites, convoques, pdfs_generes, ignores, erreurs
    """
    # 1) Parsing selon le format
    if extension in ('xlsx', 'xls'):
        colonne, lignes = _lire_lignes_xlsx(fichier)
    else:
        colonne, lignes = _lire_lignes_csv(fichier)

    if not lignes:
        raise ValidationError("Le fichier ne contient aucune donnée après l'en-tête.")

    filiere = epreuve.filiere
    heure_debut = _heure_debut_from_filiere(filiere)
    duree = epreuve.duree_minutes

    # Nombre de convocations déjà existantes (pour calculer le rang de départ)
    rang_base = epreuve.convocations.count()

    # Statuts autorisés comme candidats importables
    statuts_importables = [Dossier.Statut.ADMIS_FINAL, Dossier.Statut.PRESELECTIONNE]

    traites = 0
    convoques = 0
    pdfs_generes = 0
    ignores = 0
    erreurs = []

    with transaction.atomic():
        for i, ligne in enumerate(lignes, start=1):
            identifiant = ligne[colonne]
            traites += 1

            # 2) Retrouver le dossier par CNE / code_massar / UUID
            dossier = _chercher_dossier(identifiant, colonne, filiere, statuts_importables)

            if dossier is None:
                msg = (
                    f"Ligne {i} — '{identifiant}' : "
                    f"dossier non trouvé dans cette filière ou statut incompatible."
                )
                erreurs.append(msg)
                ignores += 1
                logger.warning(msg)
                continue

            # 3) Créer (ou récupérer) la convocation
            rang = rang_base + convoques
            heure_passage = _calculer_heure_passage(heure_debut, rang, duree)

            convocation, created = ConvocationOrale.objects.get_or_create(
                epreuve_oral=epreuve,
                dossier=dossier,
                defaults={
                    'numero_passage': rang + 1,
                    'heure_passage': heure_passage,
                    'decision': ConvocationOrale.Decision.EN_ATTENTE,
                },
            )

            if not created:
                # Déjà convoqué via ce fichier ou précédemment — on ignore
                msg = (
                    f"Ligne {i} — '{identifiant}' : déjà convoqué(e), ignoré(e)."
                )
                erreurs.append(msg)
                ignores += 1
                continue

            # 4) Changer le statut du dossier
            try:
                dossier.changer_statut(
                    Dossier.Statut.CONVOQUE_ORAL,
                    acteur=acteur,
                    commentaire=f"Convoqué via import Excel — épreuve : {epreuve.nom}",
                )
            except Exception as exc:
                erreurs.append(f"Ligne {i} — '{identifiant}' : erreur statut : {exc}")
                ignores += 1
                continue

            convoques += 1

            # 5) Générer le PDF
            try:
                generer_convocation_pdf(convocation)
                pdfs_generes += 1
            except Exception as exc:
                logger.warning("PDF non généré pour '%s' : %s", identifiant, exc)
                erreurs.append(f"Ligne {i} — '{identifiant}' : PDF non généré ({exc}).")

            # 6) Envoyer l'email (non bloquant)
            try:
                envoyer_notification(dossier, 'CONVOCATION_ORAL')
            except Exception as exc:
                logger.warning("Email non envoyé pour '%s' : %s", identifiant, exc)

        # 7) Passer l'épreuve en EN_COURS si au moins 1 candidat convoqué
        if convoques > 0 and epreuve.statut == EpreuveOrale.Statut.PLANIFIEE:
            epreuve.statut = EpreuveOrale.Statut.EN_COURS
            epreuve.save(update_fields=['statut'])

    return {
        'traites': traites,
        'convoques': convoques,
        'pdfs_generes': pdfs_generes,
        'ignores': ignores,
        'erreurs': erreurs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Recherche de dossier (CNE / code_massar / UUID)
# ─────────────────────────────────────────────────────────────────────────────

def _chercher_dossier(identifiant: str, colonne: str, filiere, statuts_importables):
    """
    Renvoie le Dossier correspondant ou None si introuvable / statut incompatible.
    Cherche par CNE, code_massar ou UUID selon `colonne`.
    """
    qs = Dossier.objects.filter(filiere=filiere, statut__in=statuts_importables)

    try:
        if colonne == 'cne':
            return qs.get(cne__iexact=identifiant)
        elif colonne == 'code_massar':
            return qs.get(code_massar__iexact=identifiant)
        elif colonne == 'id':
            return qs.get(id=identifiant)
    except Dossier.DoesNotExist:
        return None
    except (Dossier.MultipleObjectsReturned, Exception) as exc:
        logger.warning("Recherche ambiguë pour '%s' : %s", identifiant, exc)
        return None
