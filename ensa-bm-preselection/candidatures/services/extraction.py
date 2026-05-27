# candidatures/services/extraction.py
"""
Service d'extraction automatique des notes depuis les relevés PDF.

Stratégie :
  1. Extraction texte natif via pdfplumber (rapide, précis)
  2. Fallback OCR via pytesseract si le texte est vide ou de mauvaise qualité
  3. Parsing des notes avec expressions régulières
  4. Comparaison avec les notes déclarées pour détecter les fraudes
"""

from __future__ import annotations

import io
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import pdfplumber
from PIL import Image

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional dependency
    pytesseract = None

try:
    from pdf2image import convert_from_bytes
except ImportError:  # pragma: no cover - optional dependency
    convert_from_bytes = None

from django.db import transaction

from candidatures.models import Document, Dossier, NoteMatiere

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Seuils et constantes
# ──────────────────────────────────────────────────────────────────
SEUIL_CONFIANCE_PDFPLUMBER: float = 0.6
SEUIL_ECART_SUSPECT: float = 0.5

# Expressions régulières pour capturer les notes dans un relevé
# Supporte des formats comme : "Mathématiques    15.50 / 20"
#                              "Physique: 14,00/20"
#                              "Informatique ........... 17.25"
PATTERNS_NOTE: list[re.Pattern] = [
    # Format : Matière ... note /20
    re.compile(
        r"(?P<matiere>[A-ZÀ-Üa-zà-ü\s\-\'\.]+?)"   # nom matière
        r"\s*[:\.\s…]+\s*"                            # séparateur
        r"(?P<note>\d{1,2}[.,]\d{1,2})"              # note décimale
        r"\s*/?\s*(?:20)?"                            # optionnel /20
    ),
    # Format : note /20 Matière (tableaux inversés)
    re.compile(
        r"(?P<note>\d{1,2}[.,]\d{1,2})"
        r"\s*/?\s*20\s+"
        r"(?P<matiere>[A-ZÀ-Üa-zà-ü\s\-\'\.]+)"
    ),
]

# Matières courantes pour filtrer les faux positifs
MATIERES_CONNUES: set[str] = {
    "mathématiques", "math", "maths", "physique", "chimie",
    "informatique", "français", "anglais", "physique-chimie",
    "analyse", "algèbre", "mécanique", "thermodynamique",
    "électronique", "électricité", "probabilités", "statistiques",
    "optique", "svt", "sciences de la vie", "philosophie",
    "economie", "gestion", "comptabilité", "droit",
    "langue", "communication", "management",
}


# ──────────────────────────────────────────────────────────────────
# Fonctions internes
# ──────────────────────────────────────────────────────────────────


def _normaliser_matiere(raw: str) -> str:
    """Nettoie et normalise le nom d'une matière extraite."""
    matiere = raw.strip()
    # Supprimer les séparateurs résiduels en début/fin
    matiere = re.sub(r"^[\s\.\-:…]+|[\s\.\-:…]+$", "", matiere)
    # Réduire les espaces multiples
    matiere = re.sub(r"\s+", " ", matiere)
    return matiere


def _parser_note(valeur: str) -> Decimal | None:
    """Convertit une chaîne de note en Decimal, gère virgule et point."""
    try:
        valeur_normalisee = valeur.replace(",", ".")
        note = Decimal(valeur_normalisee)
        # Valider la plage [0, 20]
        if Decimal("0") <= note <= Decimal("20"):
            return note
        return None
    except (InvalidOperation, ValueError):
        return None


def _est_matiere_valide(nom: str) -> bool:
    """Vérifie si le nom ressemble à une matière scolaire connue."""
    nom_lower = nom.lower().strip()
    # Vérification directe
    if nom_lower in MATIERES_CONNUES:
        return True
    # Vérification partielle (ex: "Mathématiques Appliquées" contient "mathématiques")
    for connue in MATIERES_CONNUES:
        if connue in nom_lower or nom_lower in connue:
            return True
    # Accepter si le nom a au moins 3 caractères alphabétiques
    # (filtrer les artefacts OCR comme "1.", "a)", etc.)
    if len(re.sub(r"[^a-zA-ZÀ-ü]", "", nom)) >= 3:
        return True
    return False


def _extraire_texte_pdfplumber(contenu_pdf: bytes) -> str:
    """
    Extrait le texte natif d'un PDF via pdfplumber.

    Args:
        contenu_pdf: Contenu binaire du fichier PDF.

    Returns:
        Texte concaténé de toutes les pages.
    """
    texte_complet = ""
    try:
        with pdfplumber.open(io.BytesIO(contenu_pdf)) as pdf:
            for page in pdf.pages:
                texte_page = page.extract_text()
                if texte_page:
                    texte_complet += texte_page + "\n"
    except Exception as e:
        logger.warning("Erreur pdfplumber lors de l'extraction : %s", e)
    return texte_complet.strip()


def _extraire_texte_ocr(contenu_pdf: bytes) -> str:
    """
    Fallback OCR : convertit les pages du PDF en images
    puis applique Tesseract pour l'extraction de texte.

    Args:
        contenu_pdf: Contenu binaire du fichier PDF.

    Returns:
        Texte extrait par OCR de toutes les pages.
    """
    texte_complet = ""
    if pytesseract is None or convert_from_bytes is None:
        logger.warning(
            "OCR indisponible: pytesseract ou pdf2image n'est pas installé."
        )
        return texte_complet
    try:
        # Convertir le PDF en images (une image par page)
        images: list[Image.Image] = convert_from_bytes(
            contenu_pdf, dpi=300, fmt="png"
        )
        for i, image in enumerate(images):
            try:
                texte_page = pytesseract.image_to_string(
                    image, lang="fra", config="--psm 6"
                )
                if texte_page:
                    texte_complet += texte_page + "\n"
            except Exception as e:
                logger.warning(
                    "Erreur OCR sur la page %d : %s", i + 1, e
                )
    except Exception as e:
        logger.error("Erreur lors de la conversion PDF→images : %s", e)
    return texte_complet.strip()


def _extraire_notes_depuis_texte(texte: str) -> dict[str, Decimal]:
    """
    Parse le texte extrait pour en tirer les couples (matière, note).

    Args:
        texte: Texte brut issu de l'extraction PDF ou OCR.

    Returns:
        Dictionnaire {nom_matière_normalisé: note_decimal}.
    """
    notes: dict[str, Decimal] = {}

    for pattern in PATTERNS_NOTE:
        for match in pattern.finditer(texte):
            raw_matiere = match.group("matiere")
            raw_note = match.group("note")

            matiere = _normaliser_matiere(raw_matiere)
            note = _parser_note(raw_note)

            if note is not None and _est_matiere_valide(matiere):
                # En cas de doublon, garder la dernière occurrence
                # (souvent la note finale dans les relevés multi-semestre)
                notes[matiere.lower()] = note

    return notes


def _calculer_score_confiance(
    notes_extraites: int, notes_attendues: int
) -> float:
    """
    Calcule le ratio de confiance de l'extraction.

    Args:
        notes_extraites: Nombre de notes effectivement trouvées.
        notes_attendues: Nombre de notes déclarées dans le dossier.

    Returns:
        Score de confiance entre 0.0 et 1.0.
    """
    if notes_attendues == 0:
        # Aucune note attendue → confiance maximale par défaut
        return 1.0
    return min(notes_extraites / notes_attendues, 1.0)


# ──────────────────────────────────────────────────────────────────
# Fonction principale
# ──────────────────────────────────────────────────────────────────


@transaction.atomic
def extraire_donnees_dossier(dossier: Dossier) -> dict[str, Any]:
    """
    Extrait automatiquement les notes depuis les relevés PDF d'un dossier
    et les compare aux notes déclarées par le candidat.

    Processus :
      1. Récupère tous les documents de type RELEVE liés au dossier
      2. Pour chaque PDF :
         - Essaie pdfplumber (texte natif)
         - Si échec ou confiance faible → fallback OCR (Tesseract)
      3. Parse les notes extraites
      4. Compare avec les NoteMatiere déclarées
      5. Marque les écarts suspects

    Args:
        dossier: Instance du modèle Dossier à analyser.

    Returns:
        Dictionnaire avec les clés :
          - succes (bool): True si l'extraction a fonctionné
          - notes_extraites (int): Nombre de notes trouvées
          - score_confiance (float): Ratio notes trouvées / attendues
          - erreur (str | None): Message d'erreur le cas échéant
    """
    logger.info(
        "Début de l'extraction pour le dossier %s (candidat: %s)",
        dossier.id, dossier.candidat
    )

    # Résultat par défaut
    resultat: dict[str, Any] = {
        "succes": False,
        "notes_extraites": 0,
        "score_confiance": 0.0,
        "erreur": None,
    }

    try:
        # ── Étape 1 : Récupérer les documents RELEVE ──
        documents_releve = Document.objects.filter(
            dossier=dossier,
            type_doc=Document.TypeDocument.RELEVE,
        )

        if not documents_releve.exists():
            resultat["erreur"] = "Aucun relevé de notes trouvé dans le dossier."
            logger.warning(
                "Dossier %s : aucun document RELEVE trouvé.", dossier.id
            )
            return resultat

        # ── Étape 2 : Extraire le texte de chaque PDF ──
        texte_global = ""
        for doc in documents_releve:
            try:
                contenu_pdf = doc.fichier.read()
                if not contenu_pdf:
                    logger.warning(
                        "Document %s : fichier vide, ignoré.", doc.id
                    )
                    continue

                # Tentative pdfplumber en premier
                texte = _extraire_texte_pdfplumber(contenu_pdf)
                methode = "pdfplumber"

                # Évaluer la qualité du texte extrait
                if not texte or len(texte.strip()) < 50:
                    # Texte trop court → probablement un scan, fallback OCR
                    logger.info(
                        "Document %s : texte natif insuffisant, "
                        "basculement vers OCR.", doc.id
                    )
                    texte = _extraire_texte_ocr(contenu_pdf)
                    methode = "ocr"

                if texte:
                    texte_global += texte + "\n"
                    logger.info(
                        "Document %s : extraction réussie via %s "
                        "(%d caractères).",
                        doc.id, methode, len(texte)
                    )
                else:
                    logger.warning(
                        "Document %s : aucun texte extrait (ni natif, ni OCR).",
                        doc.id,
                    )

            except FileNotFoundError:
                logger.error(
                    "Document %s : fichier introuvable sur le disque.", doc.id
                )
            except Exception as e:
                logger.error(
                    "Document %s : erreur inattendue — %s", doc.id, e,
                    exc_info=True
                )

        if not texte_global.strip():
            resultat["erreur"] = (
                "Impossible d'extraire du texte depuis les relevés."
            )
            return resultat

        # ── Étape 3 : Parser les notes depuis le texte ──
        notes_trouvees = _extraire_notes_depuis_texte(texte_global)
        resultat["notes_extraites"] = len(notes_trouvees)

        logger.info(
            "Dossier %s : %d notes extraites du texte.",
            dossier.id, len(notes_trouvees)
        )

        # ── Étape 4 : Comparer avec les notes déclarées ──
        notes_declarees = NoteMatiere.objects.filter(dossier=dossier)
        notes_attendues = notes_declarees.count()

        dossier_suspect = False

        for note_obj in notes_declarees:
            matiere_lower = note_obj.matiere.lower().strip()

            # Chercher la correspondance dans les notes extraites
            note_extraite_val: Decimal | None = None

            # Correspondance exacte
            if matiere_lower in notes_trouvees:
                note_extraite_val = notes_trouvees[matiere_lower]
            else:
                # Correspondance partielle (ex: "math" dans "mathématiques")
                for matiere_extraite, note_val in notes_trouvees.items():
                    if (
                        matiere_lower in matiere_extraite
                        or matiere_extraite in matiere_lower
                    ):
                        note_extraite_val = note_val
                        break

            if note_extraite_val is not None:
                # Mettre à jour la note extraite dans la base
                note_obj.note_extraite = note_extraite_val

                # Calculer l'écart si la note déclarée existe
                if note_obj.note_declaree is not None:
                    ecart = abs(
                        float(note_obj.note_declaree) - float(note_extraite_val)
                    )
                    note_obj.ecart = Decimal(str(round(ecart, 2)))
                    note_obj.is_suspect = ecart > SEUIL_ECART_SUSPECT

                    if note_obj.is_suspect:
                        dossier_suspect = True
                        logger.warning(
                            "Dossier %s — matière '%s' : écart suspect "
                            "de %.2f (déclarée=%.2f, extraite=%.2f)",
                            dossier.id, note_obj.matiere,
                            ecart, note_obj.note_declaree, note_extraite_val,
                        )

                note_obj.save()

        # ── Étape 5 : Mettre à jour le dossier ──
        score_confiance = _calculer_score_confiance(
            len(notes_trouvees), notes_attendues
        )
        dossier.score_confiance_ocr = Decimal(str(round(score_confiance, 2)))
        dossier.is_suspect = dossier_suspect

        if dossier_suspect:
            logger.info(
                "Dossier %s marqué comme SUSPECT (écarts détectés).",
                dossier.id,
            )

        dossier.save(update_fields=["score_confiance_ocr", "is_suspect"])

        resultat["succes"] = True
        resultat["score_confiance"] = score_confiance

        logger.info(
            "Extraction terminée pour le dossier %s — "
            "succes=%s, notes=%d, confiance=%.2f",
            dossier.id, True, len(notes_trouvees), score_confiance,
        )

    except Exception as e:
        logger.error(
            "Erreur critique lors de l'extraction du dossier %s : %s",
            dossier.id, e, exc_info=True,
        )
        resultat["erreur"] = f"Erreur interne : {str(e)}"

    return resultat
