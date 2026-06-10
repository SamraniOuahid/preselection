# candidatures/services/regles.py
"""
Moteur de règles de rejet automatique des dossiers.

Évalue séquentiellement un ensemble de règles configurables par filière.
Dès qu'une règle échoue, le dossier est rejeté avec le motif correspondant.

Ordre d'évaluation :
  1. DOUBLON_CIN          — Détection de candidatures en double
  2. DOCUMENT_MANQUANT    — Vérification de la complétude des pièces
  3. DIPLOME_INVALIDE     — Conformité du diplôme avec les exigences
  4. ETABLISSEMENT_INVALIDE — Vérification de l'établissement d'origine
  5. MOYENNE_INSUFFISANTE — Seuil de moyenne générale
  6. NOTE_ELIMINATOIRE    — Vérification semestres (rattrapages, mentions)
  7. DATE_INCOHERENTE     — Cohérence temporelle de l'année d'obtention
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.db.models import QuerySet

from candidatures.models import Document, Dossier, NoteSemestre
from scoring.models import RegleRejet
from administration.models import DiplomaAccepte

logger = logging.getLogger(__name__)

# Ordre d'évaluation des règles (du plus éliminatoire au moins critique)
ORDRE_EVALUATION: list[str] = [
    RegleRejet.TypeRegle.DOUBLON_CIN,
    RegleRejet.TypeRegle.DOCUMENT_MANQUANT,
    RegleRejet.TypeRegle.DIPLOME_INVALIDE,
    RegleRejet.TypeRegle.ETABLISSEMENT_INVALIDE,
    RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
    RegleRejet.TypeRegle.NOTE_ELIMINATOIRE,
    RegleRejet.TypeRegle.DATE_INCOHERENTE,
]

# Types de documents obligatoires pour un dossier complet
TYPES_DOCUMENTS_OBLIGATOIRES: list[str] = [
    Document.TypeDocument.DIPLOME,
    Document.TypeDocument.RELEVE,
    Document.TypeDocument.CIN,
    Document.TypeDocument.PHOTO,
]


# ──────────────────────────────────────────────────────────────────
# Fonctions d'évaluation individuelles — une par type de règle
# ──────────────────────────────────────────────────────────────────


def _evaluer_doublon_cin(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Vérifie qu'il n'existe pas un autre dossier actif pour le même CIN
    et la même filière.

    Un doublon est détecté si un dossier (autre que le courant) existe
    pour le même candidat et la même filière avec un statut différent
    de BROUILLON.
    """
    doublons = Dossier.objects.filter(
        candidat__user__cin=dossier.candidat.user.cin,
        filiere=dossier.filiere,
    ).exclude(
        id=dossier.id,
    ).exclude(
        statut=Dossier.Statut.BROUILLON,
    )

    if doublons.exists():
        logger.warning(
            "Dossier %s : DOUBLON_CIN détecté — CIN '%s' déjà utilisé "
            "dans la filière '%s'.",
            dossier.id, dossier.candidat.user.cin, dossier.filiere.code,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.DOUBLON_CIN,
        }
    return None


def _evaluer_document_manquant(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Vérifie que les 4 types de documents obligatoires sont tous présents
    dans le dossier : DIPLOME, RELEVE, CIN, PHOTO.
    """
    types_presents: set[str] = set(
        Document.objects.filter(dossier=dossier)
        .values_list("type_doc", flat=True)
    )

    types_manquants: list[str] = [
        t for t in TYPES_DOCUMENTS_OBLIGATOIRES if t not in types_presents
    ]

    if types_manquants:
        labels = ", ".join(types_manquants)
        logger.warning(
            "Dossier %s : DOCUMENT_MANQUANT — types absents : %s",
            dossier.id, labels,
        )
        motif = f"{regle.message_rejet} (manquant(s) : {labels})"
        return {
            "rejete": True,
            "motif": motif,
            "regle": RegleRejet.TypeRegle.DOCUMENT_MANQUANT,
            "statut": Dossier.Statut.INCOMPLET,
        }
    return None


def _evaluer_diplome_invalide(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Vérifie que le diplôme déclaré par le candidat figure dans la liste
    des DiplomaAccepte actifs de la filière.

    La comparaison est insensible à la casse et accepte les correspondances
    partielles et normalisées (ex: 'dut' matche 'DUT Informatique').
    """
    if not dossier.diplome_obtenu:
        logger.warning(
            "Dossier %s : DIPLOME_INVALIDE — aucun diplôme déclaré.",
            dossier.id,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.DIPLOME_INVALIDE,
        }

    diplome_candidat = dossier.diplome_obtenu.strip().lower()

    if diplome_candidat.startswith("autre"):
        return None

    # Récupérer tous les diplômes acceptés actifs pour cette filière
    diplomes_acceptes: QuerySet[DiplomaAccepte] = (
        DiplomaAccepte.objects.filter(
            filiere=dossier.filiere,
            is_active=True,
        )
    )

    # Nettoyage et normalisation
    def clean_val(s: str) -> str:
        s = s.replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('â', 'a').replace('ï', 'i').replace('ç', 'c')
        return ''.join(c for c in s if c.isalnum())

    cleaned_candidat = clean_val(diplome_candidat)

    # Vérifier si le diplôme du candidat correspond à un diplôme accepté
    diplome_valide = False
    for da in diplomes_acceptes:
        nom_acc = da.nom_diplome.strip().lower()
        cleaned_acc = clean_val(nom_acc)
        
        # Correspondance exacte
        if nom_acc == diplome_candidat:
            diplome_valide = True
            break
            
        # Correspondance par sous-chaîne ou super-chaîne
        if cleaned_candidat in cleaned_acc or cleaned_acc in cleaned_candidat:
            diplome_valide = True
            break

    if not diplome_valide:
        logger.warning(
            "Dossier %s : DIPLOME_INVALIDE — '%s' non reconnu pour "
            "la filière '%s'.",
            dossier.id, dossier.diplome_obtenu, dossier.filiere.code,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.DIPLOME_INVALIDE,
        }
    return None


def _evaluer_etablissement_invalide(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Si la règle contient une liste d'établissements dans son paramètre,
    vérifie que l'établissement d'origine du candidat y figure.

    Si aucune liste n'est définie dans le paramètre, la règle est
    considérée comme passée (tous les établissements sont acceptés).
    """
    parametres: dict = regle.parametre or {}
    liste_etablissements: list[str] = parametres.get("etablissements", [])

    # Si la liste est vide, tous les établissements sont acceptés
    if not liste_etablissements:
        return None

    if not dossier.etablissement_origine:
        logger.warning(
            "Dossier %s : ETABLISSEMENT_INVALIDE — aucun établissement "
            "déclaré.", dossier.id,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.ETABLISSEMENT_INVALIDE,
        }

    etab_candidat = dossier.etablissement_origine.strip().lower()

    # Comparaison insensible à la casse
    etab_acceptes = [e.strip().lower() for e in liste_etablissements]

    if etab_candidat not in etab_acceptes:
        logger.warning(
            "Dossier %s : ETABLISSEMENT_INVALIDE — '%s' non reconnu.",
            dossier.id, dossier.etablissement_origine,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.ETABLISSEMENT_INVALIDE,
        }
    return None


def _evaluer_moyenne_insuffisante(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Vérifie que la moyenne générale du candidat est supérieure ou égale
    au seuil défini dans le paramètre de la règle.

    Supporte deux modes :
    - Vérification de la moyenne_generale du dossier (champ global)
    - Vérification de la moyenne des semestres (calculée à partir de NoteSemestre)
    """
    parametres: dict = regle.parametre or {}
    seuil = parametres.get("seuil")

    if seuil is None:
        logger.error(
            "Règle MOYENNE_INSUFFISANTE de la filière '%s' : "
            "paramètre 'seuil' manquant.", dossier.filiere.code,
        )
        return None  # Règle mal configurée, on ne rejette pas

    # Vérifier d'abord la moyenne générale déclarée du dossier
    if dossier.moyenne_generale is not None:
        if float(dossier.moyenne_generale) < float(seuil):
            logger.info(
                "Dossier %s : MOYENNE_INSUFFISANTE — %.2f < %.2f (seuil).",
                dossier.id, float(dossier.moyenne_generale), float(seuil),
            )
            return {
                "rejete": True,
                "motif": regle.message_rejet,
                "regle": RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
            }
        return None

    # Fallback : calculer la moyenne à partir des notes semestrielles
    notes_sem = NoteSemestre.objects.filter(dossier=dossier)
    if notes_sem.exists():
        moyenne_calculee = sum(float(n.moyenne) for n in notes_sem) / notes_sem.count()
        if moyenne_calculee < float(seuil):
            logger.info(
                "Dossier %s : MOYENNE_INSUFFISANTE (semestres) — %.2f < %.2f (seuil).",
                dossier.id, moyenne_calculee, float(seuil),
            )
            return {
                "rejete": True,
                "motif": regle.message_rejet,
                "regle": RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
            }
        return None

    # Aucune donnée de moyenne disponible
    logger.warning(
        "Dossier %s : MOYENNE_INSUFFISANTE — aucune moyenne déclarée.",
        dossier.id,
    )
    return {
        "rejete": True,
        "motif": regle.message_rejet,
        "regle": RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
    }


def _evaluer_note_eliminatoire(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Évalue les critères d'élimination basés sur les semestres :
    
    Paramètres supportés dans regle.parametre :
    - max_rattrapages (int) : nombre maximum de semestres validés en rattrapage
    - min_mentions (int) : nombre minimum de mentions ≥ ASSEZ_BIEN requises
    - min_mentions_type (str) : type minimum de mention requis (défaut: ASSEZ_BIEN)
    - matiere + seuil : ancienne logique de note éliminatoire par matière (ignorée)
    """
    parametres: dict = regle.parametre or {}

    notes_sem = NoteSemestre.objects.filter(dossier=dossier)

    if not notes_sem.exists():
        # Pas de notes semestrielles, on ignore cette règle
        logger.info(
            "Dossier %s : aucune note semestrielle, "
            "règle NOTE_ELIMINATOIRE ignorée.", dossier.id,
        )
        return None

    # ── Critère 1 : Nombre maximum de rattrapages ──
    max_rattrapages = parametres.get("max_rattrapages")
    if max_rattrapages is not None:
        nb_rattrapages = notes_sem.filter(session='RATTRAPAGE').count()
        if nb_rattrapages > int(max_rattrapages):
            motif = (
                f"{regle.message_rejet} — "
                f"Nombre de rattrapages ({nb_rattrapages}) supérieur "
                f"au maximum autorisé ({max_rattrapages})."
            )
            logger.info(
                "Dossier %s : NOTE_ELIMINATOIRE — %d rattrapages > %d max.",
                dossier.id, nb_rattrapages, int(max_rattrapages),
            )
            return {
                "rejete": True,
                "motif": motif,
                "regle": RegleRejet.TypeRegle.NOTE_ELIMINATOIRE,
            }

    # ── Critère 2 : Nombre minimum de mentions requises ──
    min_mentions = parametres.get("min_mentions")
    if min_mentions is not None:
        # Types de mentions acceptées (ASSEZ_BIEN ou mieux par défaut)
        min_type = parametres.get("min_mentions_type", "ASSEZ_BIEN")
        mentions_valides = ['TRES_BIEN', 'BIEN', 'ASSEZ_BIEN']
        if min_type == 'BIEN':
            mentions_valides = ['TRES_BIEN', 'BIEN']
        elif min_type == 'TRES_BIEN':
            mentions_valides = ['TRES_BIEN']

        nb_mentions = notes_sem.filter(mention__in=mentions_valides).count()
        if nb_mentions < int(min_mentions):
            motif = (
                f"{regle.message_rejet} — "
                f"Nombre de mentions qualifiantes ({nb_mentions}) inférieur "
                f"au minimum requis ({min_mentions})."
            )
            logger.info(
                "Dossier %s : NOTE_ELIMINATOIRE — %d mentions < %d min.",
                dossier.id, nb_mentions, int(min_mentions),
            )
            return {
                "rejete": True,
                "motif": motif,
                "regle": RegleRejet.TypeRegle.NOTE_ELIMINATOIRE,
            }

    return None


def _evaluer_date_incoherente(
    dossier: Dossier, regle: RegleRejet
) -> dict[str, Any] | None:
    """
    Vérifie que l'année d'obtention du diplôme n'est pas dans le futur.
    """
    if dossier.annee_obtention is None:
        # Pas d'année déclarée → pas de vérification possible
        return None

    annee_courante = datetime.now().year

    if dossier.annee_obtention > annee_courante:
        logger.warning(
            "Dossier %s : DATE_INCOHERENTE — année d'obtention %d "
            "supérieure à l'année courante %d.",
            dossier.id, dossier.annee_obtention, annee_courante,
        )
        return {
            "rejete": True,
            "motif": regle.message_rejet,
            "regle": RegleRejet.TypeRegle.DATE_INCOHERENTE,
        }
    return None


# ──────────────────────────────────────────────────────────────────
# Registre des évaluateurs — associe chaque type de règle à sa fonction
# ──────────────────────────────────────────────────────────────────

_EVALUATEURS: dict[str, callable] = {
    RegleRejet.TypeRegle.DOUBLON_CIN: _evaluer_doublon_cin,
    RegleRejet.TypeRegle.DOCUMENT_MANQUANT: _evaluer_document_manquant,
    RegleRejet.TypeRegle.DIPLOME_INVALIDE: _evaluer_diplome_invalide,
    RegleRejet.TypeRegle.ETABLISSEMENT_INVALIDE: _evaluer_etablissement_invalide,
    RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE: _evaluer_moyenne_insuffisante,
    RegleRejet.TypeRegle.NOTE_ELIMINATOIRE: _evaluer_note_eliminatoire,
    RegleRejet.TypeRegle.DATE_INCOHERENTE: _evaluer_date_incoherente,
}


# ──────────────────────────────────────────────────────────────────
# Fonction principale
# ──────────────────────────────────────────────────────────────────


def evaluer_regles(dossier: Dossier) -> dict[str, Any]:
    """
    Évalue toutes les règles de rejet actives pour la filière du dossier.

    Les règles sont évaluées dans un ordre prédéfini (ORDRE_EVALUATION).
    Dès qu'une règle échoue, l'évaluation s'arrête immédiatement
    et le motif de rejet est retourné.

    Args:
        dossier: Instance du modèle Dossier à évaluer.

    Returns:
        - Si rejeté : {"rejete": True, "motif": str, "regle": str}
        - Si OK     : {"rejete": False}
    """
    logger.info(
        "Début de l'évaluation des règles pour le dossier %s "
        "(filière: %s).", dossier.id, dossier.filiere.code,
    )

    try:
        # Récupérer toutes les règles actives de la filière
        regles_actives: QuerySet[RegleRejet] = RegleRejet.objects.filter(
            filiere=dossier.filiere,
            is_active=True,
        )

        if not regles_actives.exists():
            logger.info(
                "Filière '%s' : aucune règle de rejet active.",
                dossier.filiere.code,
            )
            return {"rejete": False}

        # Indexer les règles par type pour un accès O(1)
        regles_par_type: dict[str, RegleRejet] = {
            r.type_regle: r for r in regles_actives
        }

        # Évaluer dans l'ordre défini
        for type_regle in ORDRE_EVALUATION:
            regle = regles_par_type.get(type_regle)
            if regle is None:
                # Cette règle n'est pas configurée pour cette filière
                continue

            evaluateur = _EVALUATEURS.get(type_regle)
            if evaluateur is None:
                logger.error(
                    "Type de règle '%s' inconnu — aucun évaluateur trouvé.",
                    type_regle,
                )
                continue

            try:
                resultat = evaluateur(dossier, regle)
            except Exception as e:
                logger.error(
                    "Erreur lors de l'évaluation de la règle '%s' "
                    "pour le dossier %s : %s",
                    type_regle, dossier.id, e, exc_info=True,
                )
                # En cas d'erreur sur une règle, on continue les autres
                # pour ne pas bloquer le traitement
                continue

            if resultat is not None:
                # Règle échouée → rejet immédiat
                logger.info(
                    "Dossier %s : REJETÉ par la règle '%s' — %s",
                    dossier.id, type_regle, resultat["motif"],
                )
                return resultat

        # Toutes les règles sont passées avec succès
        logger.info(
            "Dossier %s : toutes les règles passées avec succès.",
            dossier.id,
        )
        return {"rejete": False}

    except Exception as e:
        logger.error(
            "Erreur critique lors de l'évaluation des règles "
            "pour le dossier %s : %s",
            dossier.id, e, exc_info=True,
        )
        # En cas d'erreur critique, ne pas rejeter automatiquement
        # mais remonter l'erreur pour traitement manuel
        raise
