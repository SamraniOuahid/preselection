# candidatures/services/__init__.py
# Point d'entrée du package services — expose les fonctions principales.

from .extraction import extraire_donnees_dossier
from .regles import evaluer_regles
from .scoring import calculer_score_dossier
from .verification_document import analyser_dossier_complet
from .fuzzy_matching import (
    identifier_categorie,
    regrouper_notes_par_categorie,
    calculer_score_pondere_filiere,
    nettoyer_bruit_ocr_note,
    POIDS_FILIERES,
    CATEGORIES_MATIERES,
)

__all__ = [
    "extraire_donnees_dossier",
    "evaluer_regles",
    "calculer_score_dossier",
    "analyser_dossier_complet",
    "identifier_categorie",
    "regrouper_notes_par_categorie",
    "calculer_score_pondere_filiere",
    "nettoyer_bruit_ocr_note",
    "POIDS_FILIERES",
    "CATEGORIES_MATIERES",
]
