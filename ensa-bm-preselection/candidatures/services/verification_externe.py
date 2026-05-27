"""
INTERFACES DE VÉRIFICATION EXTERNE — ENSA BM
═══════════════════════════════════════════════
Ces interfaces sont préparées pour une intégration future
avec les systèmes officiels marocains.

Pour activation, une convention est nécessaire entre :
  - ENSA Béni Mellal
  - Ministère de l'Éducation Nationale (Massar)
  - Direction Générale de la Sûreté Nationale (CNIE)

Contact : Ministère MEN — Direction des Systèmes d'Information
Référence légale : Loi 09-08 relative à la protection des
données personnelles au Maroc
"""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MassarVerificationService:
    """Interface de vérification via le système Massar du MEN."""

    def verifier_bac(self, cin: str, annee: int, cne: str) -> dict[str, Any]:
        """
        Vérifie les résultats du baccalauréat via Massar.
        Retourne: {'verifie': bool, 'mention': str, 'moyenne': float, ...}
        """
        raise NotImplementedError(
            "Nécessite une convention avec le MEN pour accéder à l'API Massar. "
            "Contact: Direction des Systèmes d'Information du MEN."
        )

    def verifier_diplome_superieur(self, cne: str, code_etablissement: str) -> dict[str, Any]:
        """
        Vérifie un diplôme de l'enseignement supérieur via Massar.
        Retourne: {'verifie': bool, 'diplome': str, 'annee': int, ...}
        """
        raise NotImplementedError(
            "Nécessite une convention avec le MEN pour accéder à l'API Massar."
        )


class CNIEVerificationService:
    """Interface de vérification de la CNIE via la DGSN."""

    def verifier_cin(self, numero_cin: str, nom: str, prenom: str,
                     date_naissance: str = None) -> dict[str, Any]:
        """
        Vérifie l'identité d'un citoyen via la base CNIE.
        Retourne: {'verifie': bool, 'nom_officiel': str, ...}
        """
        raise NotImplementedError(
            "Nécessite une convention avec la DGSN pour accéder à la base CNIE. "
            "Référence: Loi 09-08 relative à la protection des données personnelles."
        )


class VerificationExterneManager:
    """Orchestre les vérifications externes Massar et CNIE."""

    def __init__(self):
        self.massar = MassarVerificationService()
        self.cnie = CNIEVerificationService()

    def est_disponible(self) -> bool:
        """Retourne False tant qu'aucune convention n'est signée."""
        return False

    def verifier_dossier_complet(self, dossier) -> dict[str, Any]:
        """Vérifie un dossier via les systèmes externes."""
        if not self.est_disponible():
            return {
                'disponible': False,
                'message': (
                    'Vérification externe non disponible. '
                    'Convention MEN/DGSN requise.'
                ),
            }
        # Implémentation future une fois les conventions signées
        raise NotImplementedError("En attente des conventions institutionnelles.")
