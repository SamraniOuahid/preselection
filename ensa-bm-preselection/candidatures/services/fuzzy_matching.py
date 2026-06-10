# candidatures/services/fuzzy_matching.py
"""
Module de correspondance floue (Fuzzy Matching) pour les matières académiques.

Ce module gère :
  1. Le nettoyage du bruit OCR (lettres confondues avec des chiffres)
  2. Le dictionnaire des catégories de matières (MATH, INFO, ELEC_AUTO, etc.)
  3. La correspondance floue entre un nom de matière extrait (potentiellement
     bruité) et une catégorie connue, avec un seuil de tolérance de 80%.
  4. Le regroupement des notes extraites par catégorie pour le scoring.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from decimal import Decimal
from typing import Any

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Seuil de similarité pour le fuzzy matching (80%)
# ──────────────────────────────────────────────────────────────────
SEUIL_FUZZY: int = 80


# ──────────────────────────────────────────────────────────────────
# Catégories de matières — Dictionnaire de référence
# Chaque catégorie contient les termes connus + des patterns regex
# ──────────────────────────────────────────────────────────────────

CATEGORIES_MATIERES: dict[str, list[str]] = {
    "MATH": [
        "algèbre", "algebre", "analyse", "mathématiques", "mathematiques",
        "maths", "math", "probabilités", "probabilites", "statistiques",
        "outils scientifiques", "calcul numérique", "calcul numerique",
        "géométrie", "geometrie", "topologie", "équations différentielles",
        "equations differentielles", "analyse numérique", "analyse numerique",
    ],
    "INFO": [
        "informatique", "algorithmique", "programmation", "python",
        "langage c", "structures de données", "structures de donnees",
        "génie logiciel", "genie logiciel", "java", "c++", "base algorithmique",
        "développement", "developpement", "web", "algorithme",
        "intelligence artificielle", "système d'information",
        "systeme d'information",
    ],
    "ELEC_AUTO": [
        "automatique", "électronique", "electronique", "électrotechnique",
        "electrotechnique", "automatisme", "capteurs", "régulation",
        "regulation", "signal", "systèmes embarqués", "systemes embarques",
        "traitement du signal", "circuits", "électricité", "electricite",
        "instrumentation", "mécatronique", "mecatronique",
    ],
    "RESEAUX_BD": [
        "réseaux", "reseaux", "bases de données", "bases de donnees",
        "sql", "systèmes d'exploitation", "systemes d'exploitation",
        "architecture", "base de données", "base de donnees",
        "administration système", "administration systeme",
        "sécurité informatique", "securite informatique",
        "réseau", "reseau", "système d'exploitation",
    ],
    "CHIMIE_BIO": [
        "chimie", "biochimie", "biologie", "microbiologie",
        "thermodynamique", "procédés", "procedes", "physique",
        "chimie organique", "chimie analytique", "chimie minérale",
        "chimie minerale", "physique-chimie", "sciences de la vie",
        "svt", "optique", "mécanique", "mecanique", "transferts thermiques",
        "génie des procédés", "genie des procedes",
    ],
    "LANGUES": [
        "anglais", "communication", "tec", "français", "francais",
        "langues", "langue", "expression", "techniques d'expression",
        "communication professionnelle", "rédaction", "redaction",
    ],
}

# Créer un index inversé pour la recherche rapide : terme → catégorie
_INDEX_TERMES: dict[str, str] = {}
for _cat, _termes in CATEGORIES_MATIERES.items():
    for _terme in _termes:
        _INDEX_TERMES[_terme] = _cat


# ──────────────────────────────────────────────────────────────────
# Pondérations par filière ENSA Béni Mellal
# ──────────────────────────────────────────────────────────────────

POIDS_FILIERES: dict[str, dict[str, float]] = {
    "TDI": {
        "INFO":     0.35,
        "MATH":     0.30,
        "ELEC_AUTO": 0.25,
        "LANGUES":  0.10,
    },
    "IACS": {
        "INFO":       0.40,
        "MATH":       0.35,
        "RESEAUX_BD": 0.15,
        "LANGUES":    0.10,
    },
    "IAA": {
        "CHIMIE_BIO": 0.60,
        "MATH":       0.20,
        "INFO":       0.10,
        "LANGUES":    0.10,
    },
    "G2ER": {
        "MATH":       0.30,
        "CHIMIE_BIO": 0.30,
        "ELEC_AUTO":  0.25,
        "INFO":       0.15,
    },
}


# ──────────────────────────────────────────────────────────────────
# Fonctions de nettoyage OCR
# ──────────────────────────────────────────────────────────────────


def normaliser_unicode(texte: str) -> str:
    """Normalise les caractères Unicode (accents composés → pré-composés)."""
    return unicodedata.normalize("NFC", texte)


def nettoyer_bruit_ocr_note(valeur: str) -> str:
    """
    Nettoie les erreurs OCR courantes dans les valeurs numériques (notes).

    Conversions appliquées :
      - 'O' ou 'o' → '0' (dans un contexte numérique)
      - 'l' ou 'I' → '1' (dans un contexte numérique)
      - 'S' ou 's' → '5' (dans un contexte numérique)
      - 'B' → '8' (dans un contexte numérique)

    Args:
        valeur: Chaîne représentant une note potentiellement bruitée.

    Returns:
        Chaîne nettoyée.
    """
    # Supprimer les espaces parasites
    valeur = valeur.strip()

    # Remplacements courants lettres → chiffres dans les notes
    remplacements = {
        'O': '0', 'o': '0',
        'l': '1', 'I': '1',
        'S': '5', 's': '5',
        'B': '8',
    }

    resultat = []
    for char in valeur:
        if char in remplacements and not char.isdigit():
            # Appliquer le remplacement seulement si le caractère est
            # entouré de chiffres ou de séparateurs (virgule, point)
            resultat.append(remplacements[char])
        else:
            resultat.append(char)

    return "".join(resultat)


def nettoyer_texte_matiere(texte: str) -> str:
    """
    Nettoie un nom de matière extrait par OCR.

    - Supprime les accents pour la comparaison
    - Met en minuscules
    - Supprime les caractères parasites
    - Normalise les espaces

    Args:
        texte: Nom brut de la matière.

    Returns:
        Texte nettoyé et normalisé.
    """
    texte = normaliser_unicode(texte)
    texte = texte.lower().strip()
    # Supprimer les numérotations parasites (ex: "1. ", "a) ")
    texte = re.sub(r"^[\d]+[\.\)]\s*", "", texte)
    # Supprimer les séparateurs résiduels
    texte = re.sub(r"^[\s\.\-:…]+|[\s\.\-:…]+$", "", texte)
    # Normaliser les espaces
    texte = re.sub(r"\s+", " ", texte)
    return texte


def _supprimer_accents(texte: str) -> str:
    """Supprime les accents d'une chaîne pour la comparaison floue."""
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ──────────────────────────────────────────────────────────────────
# Correspondance floue matière → catégorie
# ──────────────────────────────────────────────────────────────────


def identifier_categorie(nom_matiere: str) -> tuple[str | None, int]:
    """
    Identifie la catégorie d'une matière par correspondance floue.

    Stratégie de recherche (du plus précis au plus tolérant) :
      1. Correspondance exacte (après nettoyage)
      2. Correspondance par sous-chaîne (un terme connu est contenu)
      3. Correspondance floue (fuzzywuzzy, seuil 80%)

    Args:
        nom_matiere: Nom de la matière extrait du relevé (peut être bruité).

    Returns:
        Tuple (catégorie, score_confiance) :
          - catégorie : "MATH", "INFO", etc. ou None si non identifié
          - score_confiance : 100 pour exact, score fuzzy sinon
    """
    nom_nettoye = nettoyer_texte_matiere(nom_matiere)
    nom_sans_accents = _supprimer_accents(nom_nettoye)

    if not nom_nettoye or len(nom_nettoye) < 2:
        return None, 0

    # ── Étape 1 : Correspondance exacte ──
    if nom_nettoye in _INDEX_TERMES:
        return _INDEX_TERMES[nom_nettoye], 100

    # Version sans accents
    for terme, cat in _INDEX_TERMES.items():
        if _supprimer_accents(terme) == nom_sans_accents:
            return cat, 100

    # ── Étape 2 : Correspondance par sous-chaîne ──
    for terme, cat in _INDEX_TERMES.items():
        terme_sans_accents = _supprimer_accents(terme)
        if (terme_sans_accents in nom_sans_accents or
                nom_sans_accents in terme_sans_accents):
            return cat, 95

    # ── Étape 3 : Correspondance floue (fuzzywuzzy) ──
    meilleur_score = 0
    meilleure_categorie = None

    for terme, cat in _INDEX_TERMES.items():
        # Utiliser partial_ratio pour gérer les sous-chaînes
        # et token_sort_ratio pour gérer les ordres différents
        score_partial = fuzz.partial_ratio(nom_sans_accents, _supprimer_accents(terme))
        score_token = fuzz.token_sort_ratio(nom_sans_accents, _supprimer_accents(terme))
        score = max(score_partial, score_token)

        if score > meilleur_score:
            meilleur_score = score
            meilleure_categorie = cat

    if meilleur_score >= SEUIL_FUZZY:
        logger.debug(
            "Fuzzy match : '%s' → catégorie '%s' (score=%d%%)",
            nom_matiere, meilleure_categorie, meilleur_score,
        )
        return meilleure_categorie, meilleur_score

    logger.debug(
        "Aucune correspondance trouvée pour '%s' (meilleur score=%d%%)",
        nom_matiere, meilleur_score,
    )
    return None, meilleur_score


# ──────────────────────────────────────────────────────────────────
# Regroupement des notes par catégorie
# ──────────────────────────────────────────────────────────────────


def regrouper_notes_par_categorie(
    notes: dict[str, Decimal],
) -> dict[str, dict[str, Any]]:
    """
    Regroupe les notes extraites par catégorie académique.

    Pour chaque matière extraite, on cherche la catégorie correspondante
    via le fuzzy matching, puis on calcule la moyenne par catégorie.

    Args:
        notes: Dictionnaire {nom_matière: note} issu de l'extraction.

    Returns:
        Dictionnaire par catégorie :
        {
            "MATH": {
                "notes": [15.5, 14.0, ...],
                "matieres": ["algèbre", "analyse", ...],
                "moyenne": 14.75,
                "nb_matieres": 2,
            },
            ...
        }
    """
    categories: dict[str, dict[str, Any]] = {}

    for matiere, note in notes.items():
        categorie, score = identifier_categorie(matiere)

        if categorie is None:
            logger.debug(
                "Matière '%s' non catégorisée (score fuzzy max=%d%%), ignorée.",
                matiere, score,
            )
            continue

        if categorie not in categories:
            categories[categorie] = {
                "notes": [],
                "matieres": [],
                "moyenne": Decimal("0.00"),
                "nb_matieres": 0,
            }

        categories[categorie]["notes"].append(float(note))
        categories[categorie]["matieres"].append(matiere)

    # Calculer les moyennes par catégorie
    for cat, data in categories.items():
        if data["notes"]:
            data["moyenne"] = round(
                sum(data["notes"]) / len(data["notes"]), 2
            )
            data["nb_matieres"] = len(data["notes"])

        logger.info(
            "Catégorie [%s] : %d matière(s) détectée(s) → "
            "moyenne = %.2f (%s)",
            cat, data["nb_matieres"], data["moyenne"],
            ", ".join(data["matieres"]),
        )

    return categories


# ──────────────────────────────────────────────────────────────────
# Calcul du score pondéré par filière
# ──────────────────────────────────────────────────────────────────


def calculer_score_pondere_filiere(
    categories_notes: dict[str, dict[str, Any]],
    code_filiere: str,
    moyenne_generale_fallback: float | None = None,
) -> dict[str, Any]:
    """
    Calcule le score pondéré final en fonction de la filière et des
    notes regroupées par catégorie.

    Formules :
      - TDI  : INFO×0.35 + MATH×0.30 + ELEC_AUTO×0.25 + LANGUES×0.10
      - IACS : INFO×0.40 + MATH×0.35 + RESEAUX_BD×0.15 + LANGUES×0.10
      - IAA  : CHIMIE_BIO×0.60 + MATH×0.20 + INFO×0.10 + LANGUES×0.10
      - G2ER : MATH×0.30 + CHIMIE_BIO×0.30 + ELEC_AUTO×0.25 + INFO×0.15

    Si une catégorie requise est introuvable :
      - Utiliser la moyenne générale comme fallback
      - Marquer le dossier pour vérification manuelle

    Args:
        categories_notes: Résultat de regrouper_notes_par_categorie().
        code_filiere: Code de la filière (ex: "TDI", "IACS", etc.).
        moyenne_generale_fallback: Moyenne des semestres à utiliser si
                                   une catégorie est manquante.

    Returns:
        Dictionnaire avec :
          - score (float): Score pondéré final
          - details (dict): Détail par catégorie
          - categories_manquantes (list): Catégories non trouvées
          - verification_manuelle (bool): True si fallback utilisé
    """
    # Extraire le code de filière simplifié (ex: "TDI-BAC2" → "TDI")
    code_simplifie = code_filiere.split("-")[0].upper().strip()

    poids = POIDS_FILIERES.get(code_simplifie)
    if poids is None:
        logger.warning(
            "Filière '%s' (simplifié: '%s') non trouvée dans les "
            "pondérations. Les filières connues sont : %s",
            code_filiere, code_simplifie, list(POIDS_FILIERES.keys()),
        )
        # Fallback : pondération uniforme sur les catégories trouvées
        if categories_notes:
            nb_cats = len(categories_notes)
            poids = {cat: 1.0 / nb_cats for cat in categories_notes}
        else:
            return {
                "score": 0.0,
                "details": {},
                "categories_manquantes": [],
                "verification_manuelle": False,
            }

    score_total = 0.0
    details: dict[str, dict[str, Any]] = {}
    categories_manquantes: list[str] = []
    verification_manuelle = False

    for categorie, poids_cat in poids.items():
        if categorie in categories_notes:
            moyenne_cat = categories_notes[categorie]["moyenne"]
            contribution = moyenne_cat * poids_cat
            details[categorie] = {
                "moyenne": moyenne_cat,
                "poids": poids_cat,
                "contribution": round(contribution, 4),
                "source": "extraction",
            }
            score_total += contribution
        else:
            # Catégorie manquante → fallback sur la moyenne générale
            categories_manquantes.append(categorie)

            if moyenne_generale_fallback is not None:
                contribution = moyenne_generale_fallback * poids_cat
                details[categorie] = {
                    "moyenne": moyenne_generale_fallback,
                    "poids": poids_cat,
                    "contribution": round(contribution, 4),
                    "source": "fallback_moyenne_generale",
                }
                score_total += contribution
                verification_manuelle = True

                logger.warning(
                    "Catégorie [%s] manquante pour la filière '%s' : "
                    "utilisation de la moyenne générale (%.2f) comme "
                    "fallback. Dossier marqué pour vérification manuelle.",
                    categorie, code_filiere, moyenne_generale_fallback,
                )
            else:
                details[categorie] = {
                    "moyenne": 0.0,
                    "poids": poids_cat,
                    "contribution": 0.0,
                    "source": "manquante",
                }
                verification_manuelle = True

                logger.warning(
                    "Catégorie [%s] manquante pour la filière '%s' et "
                    "aucune moyenne générale disponible. Contribution = 0.",
                    categorie, code_filiere,
                )

    score_total = round(min(max(score_total, 0.0), 20.0), 2)

    logger.info(
        "Score pondéré filière '%s' = %.2f (catégories manquantes : %s, "
        "vérification manuelle : %s)",
        code_filiere, score_total,
        categories_manquantes or "aucune",
        verification_manuelle,
    )

    return {
        "score": score_total,
        "details": details,
        "categories_manquantes": categories_manquantes,
        "verification_manuelle": verification_manuelle,
    }
