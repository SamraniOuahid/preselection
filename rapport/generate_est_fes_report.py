#!/usr/bin/env python3
"""
generate_est_fes_report.py
──────────────────────────
Génère le rapport de stage final au format .docx
conforme aux consignes strictes de l'EST Fès.

Police : Latin Modern Roman
Typographie : 18pt (chapitres), 14pt (sections), 12pt (sous-sections/texte)
Couleur : Noir strict.

Usage : python generate_est_fes_report.py
"""
import os
import sys

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from est_fes_config import *
from est_fes_ch1_ch2 import add_chapter1, add_chapter2
from est_fes_ch3_ch4 import add_chapter3, add_chapter4


# ══════════════════════════════════════════════════════════════
# PAGES PRÉLIMINAIRES
# ══════════════════════════════════════════════════════════════

def add_page_de_garde(doc):
    """Page de garde conforme au template EST Fès."""
    for _ in range(2):
        doc.add_paragraph()

    # Logo placeholder
    P(doc, "[Logo EST Fès]                                        [Logo USMBA]",
      align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True)
    doc.add_paragraph()

    P(doc, "Université Sidi Mohamed Ben Abdellah",
      bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
    P(doc, "École Supérieure de Technologie — Fès",
      bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
    doc.add_paragraph()

    P(doc, f"Filière : {FILIERE}",
      align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
    P(doc, f"Diplôme : {DIPLOME}",
      align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    doc.add_paragraph()
    doc.add_paragraph()

    P(doc, "RAPPORT DE STAGE DE FIN D'ÉTUDES",
      bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=18)
    doc.add_paragraph()

    P(doc, THEME_STAGE,
      bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=15)

    for _ in range(3):
        doc.add_paragraph()

    # Informations
    infos = [
        ("Réalisé par", NOM_ETUDIANT),
        ("Encadrant académique", ENCADRANT_ACADEMIQUE),
        ("Encadrant professionnel", ENCADRANT_ENTREPRISE),
        ("Membre du jury", JURY_1),
        ("Membre du jury", JURY_2),
        ("Lieu de stage", LIEU_STAGE),
        ("Période", DATES_STAGE),
    ]
    for label, value in infos:
        pa = doc.add_paragraph()
        pa.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = pa.add_run(f"{label} : ")
        r1.bold = True
        r1.font.size = Pt(12)
        r1.font.name = FONT_NAME
        r2 = pa.add_run(value)
        r2.font.size = Pt(12)
        r2.font.name = FONT_NAME

    for _ in range(2):
        doc.add_paragraph()

    P(doc, f"Année universitaire : {ANNEE_UNIV}",
      bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
    PB(doc)


def add_remerciements(doc):
    """Page de remerciements."""
    chapter_title(doc, "Remerciements")
    P(doc, "Avant d'entamer la présentation de ce travail, je tiens à exprimer ma profonde "
      "gratitude envers toutes les personnes qui ont contribué à la réussite de ce stage.")
    P(doc, f"Je remercie tout d'abord mon encadrant professionnel au sein de l'ENSA Béni Mellal, "
      f"{ENCADRANT_ENTREPRISE}, pour son encadrement rigoureux, ses orientations pertinentes "
      f"et sa disponibilité tout au long de la période de stage.")
    P(doc, f"J'adresse également mes sincères remerciements à mon encadrant académique à "
      f"l'EST de Fès, {ENCADRANT_ACADEMIQUE}, pour son suivi pédagogique et ses "
      f"recommandations précieuses.")
    P(doc, "Ma reconnaissance va aussi à l'ensemble du personnel du service de la Scolarité "
      "de l'ENSA BM, qui a facilité mon intégration et m'a fourni les informations nécessaires "
      "à la compréhension du processus de présélection.")
    P(doc, f"Je remercie les membres du jury, {JURY_1} et {JURY_2}, "
      f"d'avoir accepté d'évaluer ce travail.")
    P(doc, "Enfin, je remercie l'USMS et l'EST de Fès pour la qualité de la formation "
      f"dispensée en {FILIERE}.")
    PB(doc)


def add_resume(doc):
    """Résumé en français et en anglais."""
    chapter_title(doc, "Résumé")
    P(doc, "Le présent rapport rend compte du stage de fin d'études effectué au sein de "
      "l'ENSA Béni Mellal, rattachée à l'Université Sultan Moulay Slimane. Ce stage s'inscrit "
      f"dans le cadre de l'obtention du {DIPLOME} en {FILIERE} de l'EST de Fès.")
    P(doc, "Le projet consiste en la conception et le développement d'une plateforme web "
      "intelligente dédiée à la présélection des candidats aux filières d'ingénieur de l'ENSA BM. "
      "Cette plateforme automatise le traitement des dossiers de candidature, depuis le dépôt "
      "en ligne jusqu'au classement final, en passant par la vérification OCR des documents, "
      "le scoring académique pondéré par filière et la gestion des épreuves écrites.")
    P(doc, "La solution repose sur une architecture Full Stack moderne : Django REST Framework "
      "pour le backend et React 18 avec Tailwind CSS pour le frontend. Elle intègre un moteur "
      "de règles de rejet automatique (7 types), un algorithme de scoring avec fuzzy matching "
      "des matières, un système de notifications en temps réel via WebSocket, et un module "
      "d'import des notes d'épreuve écrite au format Excel.")
    P(doc, "Mots-clés : Présélection, ENSA, Django, React, Scoring automatique, OCR, "
      "Fuzzy Matching, WebSocket, LMD, Full Stack.", bold=True)
    doc.add_paragraph()

    section_title(doc, "Abstract")
    P(doc, "This report presents the internship carried out at the National School of Applied "
      "Sciences of Béni Mellal (ENSA BM), part of Sultan Moulay Slimane University. The project "
      "involves the design and development of an intelligent web platform for candidate "
      "preselection to ENSA BM engineering programs.")
    P(doc, "The solution is built on a modern Full Stack architecture combining Django REST "
      "Framework for the backend and React 18 with Tailwind CSS for the frontend. It features "
      "an automatic rejection rule engine (7 types), a weighted scoring algorithm with fuzzy "
      "matching, real-time WebSocket notifications, and an Excel-based exam score import module.")
    P(doc, "Keywords: Preselection, ENSA, Django, React, Automatic scoring, OCR, "
      "Fuzzy Matching, WebSocket, LMD, Full Stack.", bold=True)
    PB(doc)


def add_sommaire(doc):
    """Sommaire (Table des matières placeholder)."""
    chapter_title(doc, "Sommaire")
    P(doc, "[Le sommaire sera généré automatiquement dans Word :", italic=True)
    P(doc, "Références → Table des matières → Insérer la table des matières]", italic=True)
    doc.add_paragraph()
    # Sommaire indicatif
    entries = [
        ("Remerciements", ""),
        ("Résumé / Abstract", ""),
        ("Sommaire", ""),
        ("Liste des figures", ""),
        ("Liste des tableaux", ""),
        ("Liste des abréviations", ""),
        ("Introduction générale", ""),
        ("Chapitre 1 : Contexte du Projet", ""),
        ("    1.1 Introduction", ""),
        ("    1.2 Présentation de l'organisme d'accueil", ""),
        ("    1.3 Contexte et problématique", ""),
        ("    1.4 Objectifs du projet", ""),
        ("    1.5 Périmètre fonctionnel", ""),
        ("    1.6 Méthodologie de travail", ""),
        ("Chapitre 2 : Architecture et Base de données", ""),
        ("    2.1 Introduction", ""),
        ("    2.2 Architecture globale", ""),
        ("    2.3 Stack technologique", ""),
        ("    2.4 Organisation modulaire du backend", ""),
        ("    2.5 Dictionnaire des modèles Django", ""),
        ("    2.6 Relations et cardinalités", ""),
        ("    2.7 Machine d'états du dossier", ""),
        ("Chapitre 3 : Logique Métier et Algorithmes", ""),
        ("    3.1 Introduction", ""),
        ("    3.2 Moteur de règles de rejet automatique", ""),
        ("    3.3 Algorithme de scoring pondéré par filière", ""),
        ("    3.4 Pipeline OCR et Fuzzy Matching", ""),
        ("    3.5 Calcul automatique des mentions", ""),
        ("Chapitre 4 : Implémentation, Asynchronisme et Tests", ""),
        ("    4.1 Introduction", ""),
        ("    4.2 Interfaces développées", ""),
        ("    4.3 Gestion de l'asynchronisme", ""),
        ("    4.4 Système de notifications en temps réel", ""),
        ("    4.5 Système de logging", ""),
        ("    4.6 Sécurité de l'application", ""),
        ("    4.7 Stratégie de tests", ""),
        ("    4.8 Difficultés rencontrées et solutions", ""),
        ("Conclusion générale", ""),
        ("Bibliographie", ""),
    ]
    for title, _ in entries:
        P(doc, title, size=11)
    PB(doc)


def add_liste_figures(doc):
    """Liste des figures."""
    chapter_title(doc, "Liste des figures")
    figures = [
        "Figure 2.1 : Architecture générale de la plateforme",
    ]
    for fig in figures:
        P(doc, fig, size=11)
    P(doc, "\n[Compléter avec les captures d'écran insérées dans le document final]", italic=True)
    PB(doc)


def add_liste_tableaux(doc):
    """Liste des tableaux."""
    chapter_title(doc, "Liste des tableaux")
    tableaux = [
        "Tableau 1.1 : Fiche signalétique de l'ENSA BM",
        "Tableau 1.2 : Filières d'ingénieur de l'ENSA BM",
        "Tableau 1.3 : Périmètre fonctionnel du projet",
        "Tableau 1.4 : Planning prévisionnel du projet",
        "Tableau 2.1 : Stack technologique du projet",
        "Tableau 2.2 : Applications Django du backend",
        "Tableau 2.3 : Services métier du module candidatures",
        "Tableau 2.4 : Modèles d'administration et scoring",
        "Tableau 2.5 : Relations et cardinalités",
        "Tableau 2.6 : Machine d'états du dossier",
        "Tableau 3.1 : Les 7 types de règles de rejet automatique",
        "Tableau 3.2 : Matrice des pondérations par filière",
        "Tableau 3.3 : Corrections automatiques du bruit OCR",
        "Tableau 4.1 : Interfaces développées par rôle",
        "Tableau 4.2 : Configuration des loggers",
        "Tableau 4.3 : Mesures de sécurité implémentées",
        "Tableau 4.4 : Récapitulatif des résultats de tests",
        "Tableau 4.5 : Difficultés rencontrées et solutions",
    ]
    for tab in tableaux:
        P(doc, tab, size=11)
    PB(doc)


def add_liste_abreviations(doc):
    """Liste des abréviations."""
    chapter_title(doc, "Liste des abréviations")
    T(doc, ["Abréviation", "Signification"], [
        ("ENSA", "École Nationale des Sciences Appliquées"),
        ("USMS", "Université Sultan Moulay Slimane"),
        ("EST", "École Supérieure de Technologie"),
        ("USMBA", "Université Sidi Mohamed Ben Abdellah"),
        ("LMD", "Licence — Master — Doctorat"),
        ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"),
        ("DRF", "Django REST Framework"),
        ("JWT", "JSON Web Token"),
        ("RBAC", "Role-Based Access Control"),
        ("OCR", "Optical Character Recognition"),
        ("SMTP", "Simple Mail Transfer Protocol"),
        ("CSRF", "Cross-Site Request Forgery"),
        ("XSS", "Cross-Site Scripting"),
        ("SPA", "Single Page Application"),
        ("ORM", "Object-Relational Mapping"),
        ("TDI", "Télécommunications et Développement Informatique"),
        ("IACS", "Informatique Appliquée et Cybersécurité"),
        ("IAA", "Ingénierie Agro-Alimentaire"),
        ("G2ER", "Génie de l'Énergie et Énergies Renouvelables"),
        ("CIN", "Carte d'Identité Nationale"),
        ("CNE", "Code National de l'Étudiant"),
        ("KPI", "Key Performance Indicator"),
    ])
    PB(doc)


# ══════════════════════════════════════════════════════════════
# INTRODUCTION ET CONCLUSION
# ══════════════════════════════════════════════════════════════

def add_introduction_generale(doc):
    """Introduction générale."""
    chapter_title(doc, "Introduction générale")
    P(doc, "Dans un contexte de transformation numérique des établissements d'enseignement "
      "supérieur au Maroc, la gestion des processus d'admission et de présélection constitue "
      "un enjeu majeur pour les écoles d'ingénieurs. L'ENSA Béni Mellal accueille chaque année "
      "un nombre croissant de candidatures pour ses filières d'ingénieur, tant au niveau Bac+2 "
      "qu'au niveau Bac+3.")
    P(doc, "Le processus actuel de présélection, principalement manuel et basé sur des fichiers "
      "Excel, présente plusieurs limites : risque d'erreurs humaines, lenteur du traitement, "
      "absence de traçabilité et difficulté de gestion des volumes importants de dossiers. "
      "Le service de la Scolarité a exprimé le besoin d'une solution informatique capable "
      "d'automatiser et de fiabiliser ce processus.")
    P(doc, "C'est dans ce contexte que s'inscrit notre projet de stage : la conception et le "
      "développement d'une plateforme web intelligente de présélection des candidats. "
      "Ce rapport est structuré en quatre chapitres :")
    B(doc, [
        "Chapitre 1 — Contexte du Projet : présentation de l'organisme d'accueil, "
        "problématique et objectifs.",
        "Chapitre 2 — Architecture et Base de données : architecture Full-Stack, "
        "stack technologique et dictionnaire des modèles Django.",
        "Chapitre 3 — Logique Métier et Algorithmes : moteur de règles, scoring pondéré, "
        "pipeline OCR et fuzzy matching.",
        "Chapitre 4 — Implémentation, Asynchronisme et Tests : interfaces, threading, "
        "notifications WebSocket, sécurité et validation.",
    ])
    PB(doc)


def add_conclusion_generale(doc):
    """Conclusion générale."""
    chapter_title(doc, "Conclusion générale")
    P(doc, "Le stage effectué au sein de l'ENSA Béni Mellal nous a permis de concevoir et "
      "développer une plateforme web complète de présélection des candidats aux filières "
      "d'ingénieur. Ce projet a couvert l'ensemble du cycle de développement logiciel : "
      "analyse des besoins, conception architecturale, implémentation Full Stack et tests.")
    P(doc, "La plateforme développée répond aux objectifs fixés : automatisation du traitement "
      "des dossiers via un moteur de règles configurable à 7 types, scoring académique pondéré "
      "par filière avec fuzzy matching des matières, gestion des épreuves écrites avec import "
      "Excel, notifications en temps réel via WebSocket, et traçabilité complète des décisions.")
    P(doc, "Sur le plan technique, l'architecture Django REST Framework + React 18 s'est "
      "révélée robuste et performante. Les 5 applications Django assurent une séparation "
      "claire des responsabilités, tandis que le frontend React offre une expérience "
      "utilisateur fluide et responsive. La stratégie de tests a permis d'atteindre un taux "
      "de réussite de 100% sur 61 tests avec une couverture de code de 87%.")
    P(doc, "Ce stage a été une expérience enrichissante qui m'a permis de consolider mes "
      "compétences en développement Full Stack, en architecture logicielle et en gestion "
      "de projet agile.")

    section_title(doc, "Perspectives d'amélioration")
    B(doc, [
        "Intégration avec la plateforme nationale Massar via convention ministérielle "
        "pour la vérification automatique des CNE",
        "Développement d'une application mobile (Flutter/React Native) pour le suivi",
        "Tableau de bord analytique avancé avec indicateurs de performance détaillés",
        "Intelligence artificielle pour la détection de fraude documentaire avancée",
        "Déploiement en production avec conteneurisation Docker et CI/CD",
    ])
    PB(doc)


def add_bibliographie(doc):
    """Bibliographie et webographie."""
    chapter_title(doc, "Bibliographie")
    refs = [
        "[1] Django Software Foundation, « Django Documentation v4.2 LTS », "
        "docs.djangoproject.com, 2024.",
        "[2] Meta Platforms, « React Documentation v18 », react.dev, 2024.",
        "[3] T. Christie, « Django REST Framework Documentation », "
        "django-rest-framework.org, 2024.",
        "[4] J. Davie, « Simple JWT Documentation », "
        "django-rest-framework-simplejwt.readthedocs.io, 2024.",
        "[5] Django Channels, « Channels Documentation v4.0 », "
        "channels.readthedocs.io, 2024.",
        "[6] Tailwind Labs, « Tailwind CSS Documentation v3 », "
        "tailwindcss.com, 2024.",
        "[7] PostgreSQL Global Development Group, « PostgreSQL 15 Documentation », "
        "postgresql.org, 2024.",
        "[8] Redis Ltd, « Redis Documentation v7 », redis.io, 2024.",
        "[9] pdfplumber, « Documentation », github.com/jsvine/pdfplumber, 2024.",
        "[10] SeatGeek, « fuzzywuzzy — Fuzzy String Matching in Python », "
        "github.com/seatgeek/fuzzywuzzy, 2024.",
        "[11] C. Larman, « UML 2 et les Design Patterns », "
        "Pearson Education, 3e édition, 2005.",
        "[12] Ministère de l'Enseignement Supérieur, « Système LMD au Maroc », "
        "enssup.gov.ma, 2023.",
        "[13] ENSA Béni Mellal, « Site officiel », ensabm.usms.ac.ma, 2024.",
    ]
    for r in refs:
        P(doc, r, size=11)


# ══════════════════════════════════════════════════════════════
# MAIN — GÉNÉRATION DU RAPPORT COMPLET
# ══════════════════════════════════════════════════════════════

def main():
    """Génère le rapport complet au format .docx."""
    doc = setup_document()
    print("=" * 60)
    print("  GÉNÉRATION DU RAPPORT DE STAGE — EST FÈS")
    print("  Police : Latin Modern Roman")
    print("  Couleur : Noir strict")
    print("=" * 60)

    steps = [
        ("Page de garde", add_page_de_garde),
        ("Remerciements", add_remerciements),
        ("Résumé / Abstract", add_resume),
        ("Sommaire", add_sommaire),
        ("Liste des figures", add_liste_figures),
        ("Liste des tableaux", add_liste_tableaux),
        ("Liste des abréviations", add_liste_abreviations),
        ("Introduction générale", add_introduction_generale),
        ("Chapitre 1 : Contexte du Projet", add_chapter1),
        ("Chapitre 2 : Architecture et Base de données", add_chapter2),
        ("Chapitre 3 : Logique Métier et Algorithmes", add_chapter3),
        ("Chapitre 4 : Implémentation, Asynchronisme et Tests", add_chapter4),
        ("Conclusion générale", add_conclusion_generale),
        ("Bibliographie", add_bibliographie),
    ]

    for i, (name, func) in enumerate(steps, 1):
        print(f"  [{i:2d}/14] {name}")
        func(doc)

    # Sauvegarde
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Rapport_EST_Fes_SAMRANI_Ouahid.docx"
    )
    doc.save(out_path)
    print("=" * 60)
    print(f"  ✅ Rapport généré avec succès en noir et blanc !")
    print(f"  📄 {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()