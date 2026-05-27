# candidatures/services/scoring.py
"""
Service de calcul du score et du classement des dossiers.

Algorithme :
  1. Score pondéré = Σ (note_matière × poids / 100)
  2. Bonus mention (TB=+2, B=+1, AB=+0.5, P=+0)
  3. Score final = min(score_pondéré + bonus, 20.0)
  4. Recalcul du classement de tous les dossiers éligibles
     de la même filière (tri par score DESC puis moyenne DESC)
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db import transaction
from django.db.models import QuerySet, F

from candidatures.models import Dossier, NoteMatiere
from scoring.models import ConfigScoring

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────
SCORE_MAX: Decimal = Decimal("20.00")
SCORE_MIN: Decimal = Decimal("0.00")

# Bonus par défaut si non configuré dans ConfigScoring.bonus_mention
BONUS_MENTION_DEFAUT: dict[str, Decimal] = {
    "TB": Decimal("2.00"),
    "B": Decimal("1.00"),
    "AB": Decimal("0.50"),
    "P": Decimal("0.00"),
}

# Statuts éligibles pour le classement
STATUTS_CLASSEMENT: list[str] = [
    Dossier.Statut.EN_ATTENTE,
    Dossier.Statut.PRESELECTIONNE,
]


# ──────────────────────────────────────────────────────────────────
# Fonctions internes
# ──────────────────────────────────────────────────────────────────


def _calculer_score_pondere(
    dossier: Dossier, configs: QuerySet[ConfigScoring]
) -> Decimal:
    """
    Calcule le score pondéré à partir des notes déclarées et des poids
    configurés pour chaque matière.

    Formule : score = Σ (note_declaree × poids / 100)

    Args:
        dossier: Instance du modèle Dossier.
        configs: QuerySet des ConfigScoring de la filière.

    Returns:
        Score pondéré (Decimal).
    """
    score_total = Decimal("0.00")
    matieres_comptees = 0

    # Récupérer toutes les notes du dossier, indexées par matière (lower)
    notes_par_matiere: dict[str, NoteMatiere] = {
        n.matiere.strip().lower(): n
        for n in NoteMatiere.objects.filter(dossier=dossier)
    }

    for config in configs:
        matiere_config = config.matiere.strip().lower()

        # Recherche de la note correspondante (insensible à la casse)
        note_matiere: NoteMatiere | None = notes_par_matiere.get(
            matiere_config
        )

        if note_matiere is None:
            # Essayer une correspondance partielle
            for matiere_key, note_obj in notes_par_matiere.items():
                if matiere_config in matiere_key or matiere_key in matiere_config:
                    note_matiere = note_obj
                    break

        if note_matiere is None or note_matiere.note_declaree is None:
            logger.warning(
                "Dossier %s : matière '%s' non trouvée ou sans note "
                "déclarée — score partiel = 0 pour cette matière.",
                dossier.id, config.matiere,
            )
            continue

        # Calcul du score partiel : note × (poids / 100)
        poids_decimal = Decimal(str(config.poids)) / Decimal("100")
        score_partiel = note_matiere.note_declaree * poids_decimal

        score_total += score_partiel
        matieres_comptees += 1

        logger.debug(
            "Dossier %s — %s : %.2f × %.2f%% = %.4f",
            dossier.id, config.matiere,
            float(note_matiere.note_declaree), float(config.poids),
            float(score_partiel),
        )

    logger.info(
        "Dossier %s : score pondéré = %.4f (%d matières prises en compte).",
        dossier.id, float(score_total), matieres_comptees,
    )
    return score_total


def _obtenir_bonus_mention_valeur(
    mention: str | None, configs: QuerySet[ConfigScoring]
) -> Decimal:
    """
    Détermine le bonus à ajouter selon la mention fournie.
    """
    if not mention:
        return Decimal("0.00")

    # Chercher un bonus_mention personnalisé dans les configs
    for config in configs:
        if config.bonus_mention:
            bonus_config: dict = config.bonus_mention
            bonus_val = bonus_config.get(mention)
            if bonus_val is not None:
                return Decimal(str(bonus_val))

    # Utiliser les valeurs par défaut
    return BONUS_MENTION_DEFAUT.get(mention, Decimal("0.00"))


def _obtenir_bonus_mention(
    dossier: Dossier, configs: QuerySet[ConfigScoring]
) -> Decimal:
    """
    Détermine le bonus à ajouter selon la mention du candidat.
    """
    mention = dossier.mention
    bonus = _obtenir_bonus_mention_valeur(mention, configs)
    if not mention:
        logger.info("Dossier %s : aucune mention déclarée, bonus = 0.", dossier.id)
    else:
        logger.info(
            "Dossier %s : mention '%s' → bonus = %.2f.",
            dossier.id, mention, float(bonus),
        )
    return bonus


def _recalculer_classement(filiere_id: Any) -> int:
    """
    Recalcule le classement de tous les dossiers éligibles d'une filière.

    Critères de tri :
      1. Score DESC (plus élevé = meilleur classement)
      2. Moyenne générale DESC en cas d'égalité de score

    Args:
        filiere_id: ID de la filière (UUID).

    Returns:
        Nombre de dossiers classés.
    """
    dossiers_eligibles: QuerySet[Dossier] = (
        Dossier.objects.filter(
            filiere_id=filiere_id,
            statut__in=STATUTS_CLASSEMENT,
            score__isnull=False,
        )
        .order_by(
            F("score").desc(),
            F("moyenne_generale").desc(nulls_last=True),
        )
    )

    # Mise à jour du classement de chaque dossier
    classement_courant = 0
    dossiers_a_mettre_a_jour: list[Dossier] = []

    for dossier in dossiers_eligibles:
        classement_courant += 1
        dossier.classement = classement_courant
        dossiers_a_mettre_a_jour.append(dossier)

    # Mise à jour en masse pour optimiser les performances
    if dossiers_a_mettre_a_jour:
        Dossier.objects.bulk_update(
            dossiers_a_mettre_a_jour, ["classement"], batch_size=500
        )

    # Réinitialiser le classement des dossiers non éligibles
    # (ceux qui avaient un classement mais ne sont plus dans les statuts requis)
    Dossier.objects.filter(
        filiere_id=filiere_id,
    ).exclude(
        statut__in=STATUTS_CLASSEMENT,
    ).exclude(
        classement__isnull=True,
    ).update(classement=None)

    logger.info(
        "Filière %s : classement recalculé pour %d dossiers.",
        filiere_id, classement_courant,
    )
    return classement_courant


# ──────────────────────────────────────────────────────────────────
# Fonction principale
# ──────────────────────────────────────────────────────────────────


@transaction.atomic
def calculer_score_dossier(dossier: Dossier) -> float:
    """
    Calcule le score final d'un dossier et met à jour le classement
    de tous les dossiers éligibles de la même filière.

    Algorithme :
      1. Lire les ConfigScoring actifs de la filière
      2. Calculer le score pondéré (Σ note × poids/100)
      3. Ajouter le bonus mention (TB=+2, B=+1, AB=+0.5, P=+0)
      4. Score final = min(score_pondéré + bonus, 20.0)
      5. Sauvegarder le score dans le dossier
      6. Recalculer le classement de la filière entière

    Args:
        dossier: Instance du modèle Dossier à scorer.

    Returns:
        Score final calculé (float, entre 0.0 et 20.0).

    Raises:
        ValueError: Si aucune configuration de scoring n'est trouvée.
    """
    logger.info(
        "Début du calcul de score pour le dossier %s "
        "(candidat: %s, filière: %s).",
        dossier.id, dossier.candidat, dossier.filiere.code,
    )

    try:
        # ── Étape 1 : Récupérer les configurations de scoring ──
        configs: QuerySet[ConfigScoring] = ConfigScoring.objects.filter(
            filiere=dossier.filiere,
        )

        if not configs.exists():
            logger.warning(
                "Dossier %s : aucune configuration de scoring trouvée "
                "pour la filière '%s'. Score mis à 0.",
                dossier.id, dossier.filiere.code,
            )
            dossier.score = Decimal("0.00")
            dossier.save(update_fields=["score", "updated_at"])
            _recalculer_classement(dossier.filiere_id)
            return float(dossier.score)

        # ── Étape 2 : Calculer le score pondéré ──
        score_pondere = _calculer_score_pondere(dossier, configs)

        # ── Étape 3 : Ajouter le bonus mention ──
        bonus = _obtenir_bonus_mention(dossier, configs)

        # ── Étape 4 : Score final plafonné à 20.0 ──
        score_brut = score_pondere + bonus
        score_final = min(max(score_brut, SCORE_MIN), SCORE_MAX)

        # Arrondir à 2 décimales
        score_final = score_final.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        logger.info(
            "Dossier %s : score_pondéré=%.4f + bonus=%.2f = %.2f "
            "(final après plafonnement = %.2f).",
            dossier.id, float(score_pondere), float(bonus),
            float(score_brut), float(score_final),
        )

        # ── Étape 5 : Sauvegarder le score ──
        dossier.score = score_final
        dossier.save(update_fields=["score", "updated_at"])

        # ── Étape 6 : Recalculer le classement de la filière ──
        nb_classes = _recalculer_classement(dossier.filiere_id)
        logger.info(
            "Classement mis à jour : %d dossiers classés dans la "
            "filière '%s'.",
            nb_classes, dossier.filiere.code,
        )

        return float(score_final)

    except ValueError:
        # Re-raise les erreurs de configuration
        raise
    except Exception as e:
        logger.error(
            "Erreur critique lors du calcul du score pour le "
            "dossier %s : %s",
            dossier.id, e, exc_info=True,
        )
        raise


def calculer_score(
    notes: list[dict[str, Any]],
    configs: QuerySet[ConfigScoring],
    mention: str | None = None,
) -> float:
    """
    Calcule un score simulé à partir d'une liste de notes et d'une config.
    Utilisé par l'endpoint preview_score.
    """
    if not configs.exists():
        return 0.0

    notes_par_matiere: dict[str, Decimal] = {}
    for note in notes:
        matiere = (note.get("matiere") or "").strip()
        note_val = note.get("note") if "note" in note else note.get("note_declaree")
        if not matiere or note_val is None:
            continue
        try:
            notes_par_matiere[matiere.lower()] = Decimal(str(note_val))
        except Exception:
            continue

    score_total = Decimal("0.00")
    for config in configs:
        matiere_config = config.matiere.strip().lower()
        note_val = notes_par_matiere.get(matiere_config)
        if note_val is None:
            for matiere_key, nval in notes_par_matiere.items():
                if matiere_config in matiere_key or matiere_key in matiere_config:
                    note_val = nval
                    break
        if note_val is None:
            continue
        poids_decimal = Decimal(str(config.poids)) / Decimal("100")
        score_total += note_val * poids_decimal

    bonus = _obtenir_bonus_mention_valeur(mention, configs)
    score_final = min(max(score_total + bonus, SCORE_MIN), SCORE_MAX)
    score_final = score_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(score_final)
