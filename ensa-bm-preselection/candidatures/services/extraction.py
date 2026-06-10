# candidatures/services/extraction.py
"""
Service d'extraction automatique des notes depuis les relevés PDF.

Stratégie :
  1. Extraction texte natif via pdfplumber (rapide, précis)
  2. Fallback OCR via pytesseract si le texte est vide ou de mauvaise qualité
  3. Nettoyage du bruit OCR (lettres confondues avec des chiffres)
  4. Parsing des notes avec expressions régulières
  5. Regroupement des notes par catégorie via fuzzy matching
  6. Comparaison avec les notes déclarées pour détecter les fraudes
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

from candidatures.models import Document, Dossier, NoteSemestre
from candidatures.services.fuzzy_matching import (
    nettoyer_bruit_ocr_note,
    nettoyer_texte_matiere,
    identifier_categorie,
    regrouper_notes_par_categorie,
    calculer_score_pondere_filiere,
    CATEGORIES_MATIERES,
)

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
        r"(?P<matiere>[A-ZÀ-Üa-zà-ü\s\-\'\.\d]+?)"   # nom matière
        r"\s*[:\.\s…]+\s*"                             # séparateur
        r"(?P<note>\d{1,2}[.,]\d{1,2})"               # note décimale
        r"\s*/?\s*(?:20)?"                             # optionnel /20
    ),
    # Format : note /20 Matière (tableaux inversés)
    re.compile(
        r"(?P<note>\d{1,2}[.,]\d{1,2})"
        r"\s*/?\s*20\s+"
        r"(?P<matiere>[A-ZÀ-Üa-zà-ü\s\-\'\.\d]+)"
    ),
]

# Matières connues pour filtrer les faux positifs (élargi avec les nouvelles
# catégories du fuzzy matching)
MATIERES_CONNUES: set[str] = set()
for _termes in CATEGORIES_MATIERES.values():
    MATIERES_CONNUES.update(_termes)
# Ajouter des termes supplémentaires historiques
MATIERES_CONNUES.update({
    "mathématiques", "math", "maths", "physique", "chimie",
    "informatique", "français", "anglais", "physique-chimie",
    "analyse", "algèbre", "mécanique", "thermodynamique",
    "électronique", "électricité", "probabilités", "statistiques",
    "optique", "svt", "sciences de la vie", "philosophie",
    "economie", "gestion", "comptabilité", "droit",
    "langue", "communication", "management",
})


# ──────────────────────────────────────────────────────────────────
# Fonctions internes
# ──────────────────────────────────────────────────────────────────


def _normaliser_matiere(raw: str) -> str:
    """Nettoie et normalise le nom d'une matière extraite."""
    return nettoyer_texte_matiere(raw)


def _parser_note(valeur: str) -> Decimal | None:
    """
    Convertit une chaîne de note en Decimal, gère virgule, point
    et bruit OCR (lettres confondues avec des chiffres).
    """
    try:
        # Appliquer le nettoyage du bruit OCR sur la valeur numérique
        valeur_nettoyee = nettoyer_bruit_ocr_note(valeur)
        valeur_normalisee = valeur_nettoyee.replace(",", ".")
        note = Decimal(valeur_normalisee)
        # Valider la plage [0, 20]
        if Decimal("0") <= note <= Decimal("20"):
            return note
        return None
    except (InvalidOperation, ValueError):
        return None


def _est_matiere_valide(nom: str) -> bool:
    """
    Vérifie si le nom ressemble à une matière scolaire connue.

    Utilise le fuzzy matching pour accepter les noms bruités
    (ex: "Algebme" → reconnu via fuzzy match sur "Algèbre").
    """
    nom_lower = nom.lower().strip()

    # Vérification directe dans les matières connues
    if nom_lower in MATIERES_CONNUES:
        return True

    # Vérification partielle (ex: "Mathématiques Appliquées" contient "mathématiques")
    for connue in MATIERES_CONNUES:
        if connue in nom_lower or nom_lower in connue:
            return True

    # Vérification par fuzzy matching → la matière est identifiable dans
    # une catégorie connue
    categorie, score = identifier_categorie(nom)
    if categorie is not None:
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

    Intègre le nettoyage du bruit OCR et la validation par fuzzy
    matching des noms de matières.

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
    Extrait automatiquement les notes depuis les relevés PDF d'un dossier,
    les regroupe par catégorie via fuzzy matching, et calcule un score
    pondéré par filière si applicable.

    Processus :
      1. Récupère tous les documents de type RELEVE liés au dossier
      2. Pour chaque PDF :
         - Essaie pdfplumber (texte natif)
         - Si échec ou confiance faible → fallback OCR (Tesseract)
      3. Nettoie le bruit OCR et parse les notes extraites
      4. Regroupe les notes par catégorie (MATH, INFO, etc.) via fuzzy matching
      5. Calcule le score pondéré par filière (TDI, IACS, IAA, G2ER)
      6. Marque le dossier pour vérification manuelle si des catégories manquent

    Args:
        dossier: Instance du modèle Dossier à analyser.

    Returns:
        Dictionnaire avec les clés :
          - succes (bool): True si l'extraction a fonctionné
          - notes_extraites (int): Nombre de notes trouvées
          - score_confiance (float): Ratio notes trouvées / attendues
          - categories (dict): Notes regroupées par catégorie
          - score_filiere (dict | None): Score pondéré par filière
          - verification_manuelle (bool): True si fallback utilisé
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
        "categories": {},
        "score_filiere": None,
        "verification_manuelle": False,
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

        # ── Étape 4 : Regrouper par catégorie via fuzzy matching ──
        categories = regrouper_notes_par_categorie(notes_trouvees)
        resultat["categories"] = categories

        logger.info(
            "Dossier %s : %d catégories identifiées — %s",
            dossier.id, len(categories), list(categories.keys()),
        )

        # ── Étape 5 : Calculer le score pondéré par filière ──
        code_filiere = dossier.filiere.code if dossier.filiere else None
        moyenne_generale = None

        # Calculer la moyenne générale depuis les semestres (fallback)
        notes_semestres = NoteSemestre.objects.filter(dossier=dossier)
        if notes_semestres.exists():
            moyenne_generale = (
                sum(float(n.moyenne) for n in notes_semestres)
                / notes_semestres.count()
            )
        elif dossier.moyenne_generale is not None:
            moyenne_generale = float(dossier.moyenne_generale)

        if code_filiere and categories:
            score_filiere = calculer_score_pondere_filiere(
                categories, code_filiere, moyenne_generale
            )
            resultat["score_filiere"] = score_filiere
            resultat["verification_manuelle"] = score_filiere.get(
                "verification_manuelle", False
            )

            if resultat["verification_manuelle"]:
                logger.warning(
                    "Dossier %s : catégories manquantes (%s), "
                    "dossier marqué pour VÉRIFICATION_MANUELLE.",
                    dossier.id,
                    score_filiere.get("categories_manquantes", []),
                )

        # ── Étape 6 : Mettre à jour le dossier ──
        notes_attendues = notes_semestres.count()
        score_confiance = _calculer_score_confiance(
            len(notes_trouvees), max(notes_attendues, 1)
        )
        dossier.score_confiance_ocr = Decimal(str(round(score_confiance, 2)))

        # Marquer comme suspect si vérification manuelle requise
        if resultat["verification_manuelle"]:
            dossier.is_suspect = True

        dossier.save(update_fields=["score_confiance_ocr", "is_suspect"])

        resultat["succes"] = True
        resultat["score_confiance"] = score_confiance

        logger.info(
            "Extraction terminée pour le dossier %s — "
            "succes=%s, notes=%d, confiance=%.2f, catégories=%s",
            dossier.id, True, len(notes_trouvees), score_confiance,
            list(categories.keys()),
        )

    except Exception as e:
        logger.error(
            "Erreur critique lors de l'extraction du dossier %s : %s",
            dossier.id, e, exc_info=True,
        )
        resultat["erreur"] = f"Erreur interne : {str(e)}"

    return resultat
