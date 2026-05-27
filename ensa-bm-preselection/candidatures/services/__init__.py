# candidatures/services/__init__.py
# Point d'entrée du package services — expose les fonctions principales.

from .extraction import extraire_donnees_dossier
from .regles import evaluer_regles
from .scoring import calculer_score_dossier
from .verification_document import analyser_dossier_complet

__all__ = [
    "extraire_donnees_dossier",
    "evaluer_regles",
    "calculer_score_dossier",
    "analyser_dossier_complet",
]
