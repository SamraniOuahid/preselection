# candidatures/services/scoring.py
"""
Service de calcul du score et du classement des dossiers.

Algorithme (basé sur les semestres + pondération par filière) :
  1. Score semestriel = Moyenne des moyennes semestrielles
  2. Score pondéré par filière (via extraction OCR + fuzzy matching) :
     - TDI  : INFO×0.35 + MATH×0.30 + ELEC_AUTO×0.25 + LANGUES×0.10
     - IACS : INFO×0.40 + MATH×0.35 + RESEAUX_BD×0.15 + LANGUES×0.10
     - IAA  : CHIMIE_BIO×0.60 + MATH×0.20 + INFO×0.10 + LANGUES×0.10
     - G2ER : MATH×0.30 + CHIMIE_BIO×0.30 + ELEC_AUTO×0.25 + INFO×0.15
  3. Bonus mention (TB=+2, B=+1, AB=+0.5, P=+0)
  4. Pénalité rattrapages (configurable via ConfigScoring)
  5. Score final = min(score_pondéré + bonus - pénalités, 20.0)
  6. Recalcul du classement de tous les dossiers éligibles
     de la même filière (tri par score DESC puis moyenne DESC)
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db import transaction
from django.db.models import QuerySet, F

from candidatures.models import Dossier, NoteSemestre
from scoring.models import ConfigScoring
from candidatures.services.fuzzy_matching import (
    POIDS_FILIERES,
    identifier_categorie,
    regrouper_notes_par_categorie,
    calculer_score_pondere_filiere,
)

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

# Pénalité par semestre en rattrapage (par défaut)
PENALITE_RATTRAPAGE_DEFAUT: Decimal = Decimal("0.50")

# Statuts éligibles pour le classement
STATUTS_CLASSEMENT: list[str] = [
    Dossier.Statut.EN_ATTENTE,
    Dossier.Statut.PRESELECTIONNE,
]


# ──────────────────────────────────────────────────────────────────
# Fonctions internes
# ──────────────────────────────────────────────────────────────────


def _calculer_score_semestres(
    dossier: Dossier, configs: QuerySet[ConfigScoring]
) -> Decimal:
    """
    Calcule le score pondéré à partir des notes semestrielles.

    Formule : score = Moyenne des moyennes semestrielles

    Args:
        dossier: Instance du modèle Dossier.
        configs: QuerySet des ConfigScoring de la filière (pour compatibilité).

    Returns:
        Score pondéré (Decimal).
    """
    notes_semestres = NoteSemestre.objects.filter(dossier=dossier)

    if not notes_semestres.exists():
        # Fallback : utiliser la moyenne générale déclarée si aucun semestre
        if dossier.moyenne_generale is not None:
            logger.info(
                "Dossier %s : aucun semestre, utilisation de la moyenne "
                "générale déclarée = %.2f.",
                dossier.id, float(dossier.moyenne_generale),
            )
            return Decimal(str(dossier.moyenne_generale))

        logger.warning(
            "Dossier %s : aucun semestre et aucune moyenne déclarée. "
            "Score mis à 0.", dossier.id,
        )
        return Decimal("0.00")

    # Calcul de la moyenne des semestres
    total = sum(Decimal(str(n.moyenne)) for n in notes_semestres)
    nb_semestres = notes_semestres.count()
    score_moyen = total / Decimal(str(nb_semestres))

    logger.info(
        "Dossier %s : score semestriel = %.4f (%d semestres).",
        dossier.id, float(score_moyen), nb_semestres,
    )

    return score_moyen


def _calculer_penalite_rattrapages(
    dossier: Dossier, configs: QuerySet[ConfigScoring]
) -> Decimal:
    """
    Calcule la pénalité liée aux semestres validés en rattrapage.

    Args:
        dossier: Instance du modèle Dossier.
        configs: QuerySet des ConfigScoring de la filière.

    Returns:
        Pénalité totale (Decimal, valeur positive à soustraire).
    """
    nb_rattrapages = NoteSemestre.objects.filter(
        dossier=dossier, session='RATTRAPAGE'
    ).count()

    if nb_rattrapages == 0:
        return Decimal("0.00")

    # Chercher une pénalité personnalisée dans les configs
    penalite_par_rattrapage = PENALITE_RATTRAPAGE_DEFAUT
    for config in configs:
        if config.bonus_mention and 'penalite_rattrapage' in config.bonus_mention:
            penalite_par_rattrapage = Decimal(
                str(config.bonus_mention['penalite_rattrapage'])
            )
            break

    penalite = penalite_par_rattrapage * Decimal(str(nb_rattrapages))

    logger.info(
        "Dossier %s : pénalité rattrapages = %.2f "
        "(%d × %.2f).",
        dossier.id, float(penalite), nb_rattrapages,
        float(penalite_par_rattrapage),
    )

    return penalite


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
def _obtenir_coefficient_diplome(dossier: Dossier) -> Decimal:
    """
    Récupère le coefficient lié au diplôme du dossier.
    Si le diplôme commence par 'autre' ou n'est pas dans la liste des diplômes acceptés,
    on utilise le coef_autre_diplome de la filière.
    """
    diplome = (dossier.diplome_obtenu or "").strip().lower()
    if not diplome:
        return Decimal("1.00")
        
    if diplome.startswith("autre"):
        return Decimal(str(dossier.filiere.coef_autre_diplome))

    diplomes_acceptes = dossier.filiere.diplomes_acceptes.filter(is_active=True)

    # Si aucun diplôme accepté n'est configuré pour cette filière (par ex. dans les tests), pas de pénalité
    if not diplomes_acceptes.exists():
        return Decimal("1.00")

    # Nettoyage et normalisation
    def clean_val(s: str) -> str:
        s = s.replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('â', 'a').replace('ï', 'i').replace('ç', 'c')
        return ''.join(c for c in s if c.isalnum())

    cleaned_candidat = clean_val(diplome)
    for da in diplomes_acceptes:
        nom_acc = da.nom_diplome.strip().lower()
        cleaned_acc = clean_val(nom_acc)
        if nom_acc == diplome or cleaned_candidat in cleaned_acc or cleaned_acc in cleaned_candidat:
            return Decimal(str(da.coefficient))

    # Si non trouvé dans les acceptés
    return Decimal(str(dossier.filiere.coef_autre_diplome))


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
      2. Calculer la moyenne des semestres
      3. Ajouter le bonus mention (TB=+2, B=+1, AB=+0.5, P=+0)
      4. Soustraire la pénalité rattrapages
      5. Appliquer le coefficient du diplôme (ou coef autre diplôme)
      6. Score final = min(max(score, 0), 20.0) * coefficient
      7. Sauvegarder le score dans le dossier
      8. Recalculer le classement de la filière entière

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

        # ── Étape 2 : Calculer le score semestriel ──
        score_pondere = _calculer_score_semestres(dossier, configs)

        # ── Étape 3 : Ajouter le bonus mention ──
        bonus = _obtenir_bonus_mention(dossier, configs)

        # ── Étape 3b : Soustraire la pénalité rattrapages ──
        penalite = _calculer_penalite_rattrapages(dossier, configs)

        # ── Étape 4 : Appliquer le coefficient du diplôme ──
        coef = _obtenir_coefficient_diplome(dossier)
        score_brut = (score_pondere + bonus - penalite) * coef
        score_final = min(max(score_brut, SCORE_MIN), SCORE_MAX)

        # Arrondir à 2 décimales
        score_final = score_final.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        logger.info(
            "Dossier %s : (score_sem=%.4f + bonus=%.2f - penalite=%.2f) "
            "* coef=%.2f = %.2f (final après plafonnement = %.2f).",
            dossier.id, float(score_pondere), float(bonus),
            float(penalite), float(coef),
            float(score_brut), float(score_final),
        )

        # ── Étape 5 : Mettre à jour la moyenne générale ──
        # Synchroniser la moyenne_generale avec la moyenne des semestres
        notes_sem = NoteSemestre.objects.filter(dossier=dossier)
        if notes_sem.exists():
            moy = sum(float(n.moyenne) for n in notes_sem) / notes_sem.count()
            dossier.moyenne_generale = Decimal(str(round(moy, 2)))

        # ── Étape 6 : Sauvegarder le score ──
        dossier.score = score_final
        dossier.save(update_fields=["score", "moyenne_generale", "updated_at"])

        # ── Étape 7 : Recalculer le classement de la filière ──
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
    diplome: str | None = None,
    filiere_obj=None,
) -> float:
    """
    Calcule un score simulé à partir d'une liste de notes semestrielles et d'une config.
    Utilisé par l'endpoint preview_score.
    
    Accepte les formats :
    - Semestres : [{"semestre": "S1", "moyenne": 14, "session": "NORMALE", "mention": "BIEN"}, ...]
    - Legacy matières : [{"matiere": "Math", "note": 15}, ...]

    Pour le format legacy matières, le fuzzy matching est utilisé pour regrouper
    les notes par catégorie et appliquer la pondération par filière si applicable.
    """
    if not notes:
        return 0.0

    # Détecter si les notes sont au format semestre ou matière
    is_semestre_format = any('semestre' in n or 'moyenne' in n for n in notes)

    if is_semestre_format:
        # Format semestre
        moyennes = []
        nb_rattrapages = 0
        for note in notes:
            moy = note.get("moyenne")
            if moy is None:
                continue
            try:
                moyennes.append(Decimal(str(moy)))
            except Exception:
                continue
            if note.get("session") == "RATTRAPAGE":
                nb_rattrapages += 1

        if not moyennes:
            return 0.0

        score_total = sum(moyennes) / Decimal(str(len(moyennes)))

        # Pénalité rattrapages
        penalite = PENALITE_RATTRAPAGE_DEFAUT * Decimal(str(nb_rattrapages))
        for config in configs:
            if config.bonus_mention and 'penalite_rattrapage' in config.bonus_mention:
                penalite = Decimal(str(config.bonus_mention['penalite_rattrapage'])) * Decimal(str(nb_rattrapages))
                break

    else:
        # Format legacy matières — avec fuzzy matching par catégorie
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

        # Essayer d'utiliser le scoring par filière via fuzzy matching
        code_filiere = filiere_obj.code if filiere_obj else None
        code_simplifie = (
            code_filiere.split("-")[0].upper().strip() if code_filiere else None
        )

        if code_simplifie and code_simplifie in POIDS_FILIERES and notes_par_matiere:
            # Regrouper les notes par catégorie via fuzzy matching
            categories = regrouper_notes_par_categorie(notes_par_matiere)

            if categories:
                # Calculer la moyenne générale comme fallback
                moyenne_fallback = None
                if notes_par_matiere:
                    moyenne_fallback = float(
                        sum(notes_par_matiere.values())
                        / Decimal(str(len(notes_par_matiere)))
                    )

                result_filiere = calculer_score_pondere_filiere(
                    categories, code_filiere, moyenne_fallback
                )
                score_total = Decimal(str(result_filiere["score"]))
            else:
                # Aucune catégorie identifiée, fallback sur la moyenne simple
                if notes_par_matiere:
                    score_total = sum(notes_par_matiere.values()) / Decimal(
                        str(len(notes_par_matiere))
                    )
                else:
                    score_total = Decimal("0.00")
        else:
            # Pas de filière connue ou pas de notes, utiliser l'ancien calcul
            score_total = Decimal("0.00")
            if configs.exists():
                for config in configs:
                    matiere_config = config.matiere.strip().lower()
                    note_val = notes_par_matiere.get(matiere_config)
                    if note_val is None:
                        # Essayer le fuzzy matching sur les matières de la config
                        for matiere_key, nval in notes_par_matiere.items():
                            cat_config, _ = identifier_categorie(matiere_config)
                            cat_key, _ = identifier_categorie(matiere_key)
                            if cat_config and cat_key and cat_config == cat_key:
                                note_val = nval
                                break
                            # Fallback : correspondance par sous-chaîne
                            if (matiere_config in matiere_key
                                    or matiere_key in matiere_config):
                                note_val = nval
                                break
                    if note_val is None:
                        continue
                    poids_decimal = Decimal(str(config.poids)) / Decimal("100")
                    score_total += note_val * poids_decimal
            elif notes_par_matiere:
                # Pas de configs, moyenne simple
                score_total = sum(notes_par_matiere.values()) / Decimal(str(len(notes_par_matiere)))

        penalite = Decimal("0.00")

    bonus = _obtenir_bonus_mention_valeur(mention, configs)
    
    # Détermination du coefficient pour la simulation
    coef = Decimal("1.00")
    if filiere_obj and diplome:
        diplome_cleaned = diplome.strip().lower()
        if diplome_cleaned.startswith("autre"):
            coef = Decimal(str(filiere_obj.coef_autre_diplome))
        else:
            diplomes_acceptes = filiere_obj.diplomes_acceptes.filter(is_active=True)
            if not diplomes_acceptes.exists():
                coef = Decimal("1.00")
            else:
                def clean_val(s: str) -> str:
                    s = s.replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('â', 'a').replace('ï', 'i').replace('ç', 'c')
                    return ''.join(c for c in s if c.isalnum())
                cleaned_candidat = clean_val(diplome_cleaned)
                found = False
                for da in diplomes_acceptes:
                    nom_acc = da.nom_diplome.strip().lower()
                    cleaned_acc = clean_val(nom_acc)
                    if nom_acc == diplome_cleaned or cleaned_candidat in cleaned_acc or cleaned_acc in cleaned_candidat:
                        coef = Decimal(str(da.coefficient))
                        found = True
                        break
                if not found:
                    coef = Decimal(str(filiere_obj.coef_autre_diplome))

    score_final = min(max((score_total + bonus - penalite) * coef, SCORE_MIN), SCORE_MAX)
    score_final = score_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(score_final)
