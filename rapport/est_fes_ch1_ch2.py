"""Chapitres 1 et 2 du rapport EST Fès."""
from est_fes_config import *


def add_chapter1(doc):
    """Chapitre 1 : Contexte du Projet."""
    chapter_title(doc, "Chapitre 1 : Contexte du Projet")

    section_title(doc, "1.1 Introduction")
    P(doc, "Ce chapitre présente le cadre général dans lequel s'inscrit notre stage de fin d'études. "
      "Nous y décrivons l'organisme d'accueil, le contexte institutionnel, la problématique identifiée "
      "et les objectifs du projet.")

    section_title(doc, "1.2 Présentation de l'organisme d'accueil")
    subsection_title(doc, "1.2.1 L'ENSA Béni Mellal")
    P(doc, "L'École Nationale des Sciences Appliquées de Béni Mellal (ENSA BM) est un établissement "
      "public d'enseignement supérieur rattaché à l'Université Sultan Moulay Slimane (USMS). "
      "Créée en 2003 par décret ministériel n° 2-03-200, elle fait partie du réseau des douze ENSA "
      "marocaines et forme des ingénieurs d'État dans les domaines des sciences appliquées.")
    T(doc, ["Rubrique", "Information"], [
        ("Dénomination", "École Nationale des Sciences Appliquées de Béni Mellal"),
        ("Sigle", "ENSA BM"),
        ("Université", "Université Sultan Moulay Slimane (USMS)"),
        ("Statut", "Établissement public d'enseignement supérieur"),
        ("Création", "2003 — Décret n° 2-03-200"),
        ("Effectif étudiants", "~2 500 (2024-2025)"),
        ("Enseignants", "~120 enseignants-chercheurs"),
    ], caption="Tableau 1.1 : Fiche signalétique de l'ENSA BM")

    subsection_title(doc, "1.2.2 Missions et offre de formation")
    P(doc, "L'ENSA BM a pour mission de former des ingénieurs d'État polyvalents, de développer "
      "la recherche scientifique et l'innovation technologique, et de contribuer au développement "
      "socio-économique de la région Béni Mellal-Khénifra.")
    P(doc, "L'école propose quatre filières d'ingénieur accessibles aux niveaux Bac+2 et Bac+3 :")
    T(doc, ["Code", "Filière", "Places"], [
        ("TDI", "Télécommunications et Développement Informatique", "30"),
        ("IACS", "Informatique Appliquée et Cybersécurité", "30"),
        ("IAA", "Ingénierie Agro-Alimentaire", "30"),
        ("G2ER", "Génie de l'Énergie et Énergies Renouvelables", "30"),
    ], caption="Tableau 1.2 : Filières d'ingénieur de l'ENSA BM")

    subsection_title(doc, "1.2.3 Service de la Scolarité")
    P(doc, "Le service de la Scolarité gère l'ensemble des processus administratifs liés aux étudiants : "
      "inscriptions, examens, stages, diplomation et présélection des candidats au cycle ingénieur. "
      "C'est le principal bénéficiaire et commanditaire de notre plateforme.")

    section_title(doc, "1.3 Contexte et problématique")
    subsection_title(doc, "1.3.1 Le processus actuel de présélection")
    P(doc, "Le processus actuel de présélection à l'ENSA BM se déroule en plusieurs étapes manuelles : "
      "(1) réception des dossiers physiques ou par email, (2) vérification manuelle de la conformité "
      "des pièces, (3) saisie des notes dans un fichier Excel, (4) tri et classement manuel, "
      "(5) convocation à l'épreuve écrite, et (6) saisie des notes d'épreuve et classement final. "
      "Ce processus mobilise plusieurs agents pendant plusieurs semaines.")

    subsection_title(doc, "1.3.2 Problèmes identifiés")
    B(doc, [
        "Traitement lent et chronophage : plusieurs semaines pour quelques centaines de dossiers",
        "Risque élevé d'erreurs de saisie lors de la transcription manuelle des notes",
        "Absence totale de traçabilité des décisions prises",
        "Manque de transparence : les candidats n'ont aucune visibilité sur l'état de leur dossier",
        "Doublons non détectés : difficulté d'identifier les candidatures multiples",
        "Classement approximatif : calculs manuels sujets à erreur",
    ])

    subsection_title(doc, "1.3.3 Le système LMD marocain")
    P(doc, "Le système LMD marocain structure les études supérieures en trois cycles. Chaque semestre "
      "est évalué sur 20 points. Les mentions sont attribuées selon les seuils suivants :")
    T(doc, ["Moyenne", "Mention"], [
        ("≥ 16.00", "Très Bien"), ("≥ 14.00", "Bien"),
        ("≥ 12.00", "Assez Bien"), ("≥ 10.00", "Passable"),
    ])
    P(doc, "Notre plateforme doit impérativement respecter ces seuils pour le calcul automatique "
      "des mentions et du scoring académique.")

    section_title(doc, "1.4 Objectifs du projet")
    subsection_title(doc, "1.4.1 Objectif principal")
    P(doc, "Concevoir et développer une plateforme web complète permettant d'automatiser et de "
      "fiabiliser le processus de présélection des candidats aux filières d'ingénieur de l'ENSA BM.")

    subsection_title(doc, "1.4.2 Objectifs spécifiques")
    B(doc, [
        "Automatisation du rejet des dossiers non conformes via un moteur de règles configurable",
        "Scoring académique pondéré par filière avec fuzzy matching des matières",
        "Classement automatique des candidats intégrant dossier (40%) et épreuve écrite (60%)",
        "Notifications en temps réel via WebSocket et email SMTP",
        "Traçabilité et audit complet du processus de présélection",
        "Import des notes d'épreuve écrite au format Excel",
    ])

    section_title(doc, "1.5 Périmètre fonctionnel")
    T(doc, ["Fonctionnalité", "Inclus"], [
        ("Inscription et authentification JWT", "Oui"),
        ("Dépôt de dossier multi-étapes", "Oui"),
        ("Moteur de règles de rejet automatique", "Oui"),
        ("Scoring pondéré par filière", "Oui"),
        ("Dashboard responsable avec KPIs", "Oui"),
        ("Import notes Excel", "Oui"),
        ("Notifications WebSocket + SMTP", "Oui"),
        ("Export résultats Excel", "Oui"),
        ("Application mobile native", "Non (hors scope)"),
        ("Intégration Massar", "Non (hors scope)"),
    ], caption="Tableau 1.3 : Périmètre fonctionnel du projet")

    section_title(doc, "1.6 Méthodologie de travail")
    P(doc, "Nous avons adopté une approche agile itérative, organisée en sprints hebdomadaires "
      "sur 4 semaines. Chaque sprint produit un incrément fonctionnel testé et validé.")
    T(doc, ["Semaine", "Phase", "Livrables"], [
        ("S1", "Fondations Backend", "Modèles Django, API REST, Auth JWT"),
        ("S2", "Intelligence métier", "Moteur de règles, Scoring, OCR"),
        ("S3", "Frontend React", "Pages candidat, Dashboard, Formulaires"),
        ("S4", "Tests et finalisation", "Tests, Corrections, Documentation"),
    ], caption="Tableau 1.4 : Planning prévisionnel du projet")

    section_title(doc, "1.7 Conclusion")
    P(doc, "Ce chapitre a permis de situer le cadre institutionnel de notre stage et de définir "
      "clairement la problématique et les objectifs du projet. Le chapitre suivant présentera "
      "l'architecture technique et le modèle de données de la plateforme.")
    PB(doc)


def add_chapter2(doc):
    """Chapitre 2 : Architecture et Base de données."""
    chapter_title(doc, "Chapitre 2 : Architecture et Base de données")

    section_title(doc, "2.1 Introduction")
    P(doc, "Ce chapitre détaille l'architecture technique de la plateforme, le choix des technologies, "
      "l'organisation modulaire du code et le dictionnaire complet des modèles Django.")

    section_title(doc, "2.2 Architecture globale")
    subsection_title(doc, "2.2.1 Vue d'ensemble")
    P(doc, "L'application repose sur une architecture moderne Full-Stack Client-Serveur à trois niveaux :")
    B(doc, [
        "Frontend : React 18 compilé via Vite, avec Tailwind CSS pour le rendu responsive. "
        "L'architecture s'appuie sur des composants réutilisables, React Router v6 et un state "
        "management optimisé via Context API.",
        "Backend : Django 4.2 LTS et Django REST Framework (DRF), exposant une API REST sécurisée "
        "par JWT (SimpleJWT). Le backend est organisé en 5 applications Django indépendantes.",
        "Base de données : PostgreSQL 15 géré par l'ORM Django, assurant la persistance des "
        "candidatures, configurations et historiques.",
        "Temps réel : Django Channels 4.0 avec Redis comme channel layer pour les WebSockets "
        "(notifications en temps réel avec barre de progression).",
    ])
    FIG(doc, "Figure 2.1 : Architecture générale de la plateforme")

    subsection_title(doc, "2.2.2 Architecture REST stateless")
    P(doc, "Le frontend communique avec le backend exclusivement via des endpoints REST sécurisés "
      "par JWT. Les réponses sont au format JSON. Le pattern est strictement stateless côté serveur, "
      "à l'exception des connexions WebSocket persistantes pour les notifications.")

    section_title(doc, "2.3 Stack technologique")
    T(doc, ["Technologie", "Version", "Rôle"], [
        ("Django", "4.2 LTS", "Framework backend principal"),
        ("Django REST Framework", "3.17", "Construction de l'API REST"),
        ("Django Channels", "4.0", "WebSockets temps réel"),
        ("SimpleJWT", "5.5", "Authentification par tokens JWT"),
        ("React", "18", "Framework frontend SPA"),
        ("Tailwind CSS", "3.x", "Framework CSS utilitaire"),
        ("PostgreSQL", "15", "Base de données relationnelle"),
        ("Redis", "7.x", "Channel Layer WebSocket"),
        ("pdfplumber + pytesseract", "—", "Extraction OCR"),
        ("fuzzywuzzy", "0.18", "Correspondance floue des matières"),
        ("openpyxl", "—", "Import/Export Excel"),
    ], caption="Tableau 2.1 : Stack technologique du projet")

    section_title(doc, "2.4 Organisation modulaire du backend")
    P(doc, "Le backend est structuré en 5 applications Django indépendantes, chacune gérant "
      "un domaine métier spécifique :")
    T(doc, ["Application", "Responsabilité", "Fichiers clés"], [
        ("users", "Authentification, comptes, profils candidats", "models.py, serializers.py, views.py"),
        ("candidatures", "Dossiers, documents, notes, services métier", "models.py, views.py, services/"),
        ("administration", "Filières, diplômes, épreuves, historique", "models.py, views.py"),
        ("scoring", "Règles de rejet, configuration scoring", "models.py, views.py"),
        ("notifications", "Notifications email et WebSocket", "models.py, consumers.py, views.py"),
    ], caption="Tableau 2.2 : Applications Django du backend")

    P(doc, "Le répertoire candidatures/services/ contient la logique métier critique :")
    T(doc, ["Service", "Fichier", "Rôle"], [
        ("Extraction OCR", "extraction.py", "Extraction des informations depuis les documents scannés"),
        ("Fuzzy Matching", "fuzzy_matching.py", "Correspondance floue des noms de matières"),
        ("Règles de rejet", "regles.py", "Application des 7 types de règles de rejet automatique"),
        ("Scoring", "scoring.py", "Calcul du score pondéré par filière"),
        ("Vérification", "verification_document.py", "Vérification d'authenticité des documents"),
        ("Invitation PDF", "invitation_pdf.py", "Génération des convocations au format PDF"),
    ], caption="Tableau 2.3 : Services métier du module candidatures")

    section_title(doc, "2.5 Dictionnaire des modèles Django")
    P(doc, "Le modèle relationnel est structuré autour de 12 entités principales réparties "
      "dans les applications Django. Nous détaillons ci-dessous chaque modèle.")

    subsection_title(doc, "2.5.1 Application Users")
    P(doc, "Le modèle User étend AbstractBaseUser de Django pour personnaliser l'authentification. "
      "L'identification se fait par email et CIN (Carte d'Identité Nationale). Trois rôles sont "
      "définis : CANDIDAT, RESPONSABLE et ADMIN, implémentant un contrôle d'accès RBAC.")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire auto-générée"),
        ("email", "VARCHAR", "UNIQUE, NOT NULL"),
        ("cin", "VARCHAR", "UNIQUE, NOT NULL"),
        ("role", "ENUM", "CANDIDAT / RESPONSABLE / ADMIN"),
        ("is_active", "BOOLEAN", "Défaut : True"),
        ("password", "VARCHAR", "Hashé via PBKDF2"),
    ])
    P(doc, "Le modèle Candidat est relié en OneToOne à User et stocke le profil détaillé :")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire"),
        ("user_id", "FK → User", "OneToOne, CASCADE"),
        ("nom", "VARCHAR", "NOT NULL"),
        ("prenom", "VARCHAR", "NOT NULL"),
        ("telephone", "VARCHAR", "Optionnel"),
        ("date_naissance", "DATE", "NOT NULL"),
    ])

    subsection_title(doc, "2.5.2 Application Candidatures")
    P(doc, "Le modèle Dossier est le modèle central de l'application. Il lie un Candidat à une "
      "Filière et contient le statut, les scores calculés et les motifs de rejet éventuels.")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire"),
        ("candidat_id", "FK → Candidat", "CASCADE"),
        ("filiere_id", "FK → Filiere", "CASCADE"),
        ("statut", "ENUM", "11 valeurs possibles"),
        ("score", "DECIMAL", "Score dossier calculé"),
        ("score_final", "DECIMAL", "40% dossier + 60% épreuve"),
        ("rang_final", "INT", "Classement par filière"),
        ("mention", "ENUM", "Auto-calculé"),
        ("moyenne_generale", "DECIMAL", "Moyenne des semestres"),
    ])

    P(doc, "Le modèle Document gère les pièces justificatives uploadées par le candidat :")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire"),
        ("dossier_id", "FK → Dossier", "CASCADE"),
        ("type_doc", "ENUM", "DIPLOME / RELEVE / CIN / PHOTO"),
        ("fichier", "FILE", "Stocké dans media/dossiers/{uuid}/"),
        ("qualite_ocr", "DECIMAL", "Score de confiance OCR"),
    ])

    P(doc, "Le modèle NoteSemestre remplace l'ancienne approche par NoteMatiere. Il intègre "
      "la moyenne par semestre, la session et la mention calculée dynamiquement :")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire"),
        ("dossier_id", "FK → Dossier", "CASCADE"),
        ("semestre", "ENUM", "S1 à S6"),
        ("moyenne", "DECIMAL", "Plage stricte [10.00, 20.00]"),
        ("session", "ENUM", "NORMALE / RATTRAPAGE"),
        ("mention", "ENUM", "Auto-calculé (editable=False)"),
    ])

    subsection_title(doc, "2.5.3 Application Administration et Scoring")
    P(doc, "Le modèle Filiere définit les filières du cycle ingénieur avec leurs paramètres :")
    T(doc, ["Attribut", "Type", "Contrainte"], [
        ("id", "UUID", "Clé primaire"),
        ("nom", "VARCHAR", "NOT NULL"),
        ("code", "VARCHAR", "UNIQUE (TDI, IACS, IAA, G2ER)"),
        ("niveau", "ENUM", "BAC2 / BAC3"),
        ("places_disponibles", "INT", "Défaut : 30"),
    ])

    P(doc, "Les modèles EpreuveEcrite et NoteEcrite gèrent la logistique du concours écrit :")
    T(doc, ["Modèle", "Attributs clés", "Rôle"], [
        ("EpreuveEcrite", "nom, date_epreuve, seuil_admission, statut", "Gestion de l'épreuve par filière"),
        ("NoteEcrite", "note, resultat, rang_final", "Note individuelle et classement"),
        ("ConfigScoring", "matiere, poids, bonus_mention", "Pondération scoring par filière"),
        ("RegleRejet", "type_regle, parametre, is_active, message", "Règle de rejet configurable"),
        ("HistoriqueAction", "action, commentaire, timestamp", "Traçabilité des décisions"),
    ], caption="Tableau 2.4 : Modèles d'administration et scoring")

    section_title(doc, "2.6 Relations et cardinalités")
    T(doc, ["Relation", "Type", "Cardinalité"], [
        ("User → Candidat", "OneToOne", "1..1"),
        ("Candidat → Dossier", "OneToMany", "1..*"),
        ("Dossier → Document", "OneToMany", "1..4"),
        ("Dossier → NoteSemestre", "OneToMany", "1..6"),
        ("Filiere → Dossier", "OneToMany", "1..*"),
        ("Filiere → RegleRejet", "OneToMany", "1..*"),
        ("Filiere → EpreuveEcrite", "OneToMany", "1..*"),
        ("EpreuveEcrite → NoteEcrite", "OneToMany", "1..*"),
        ("Dossier → HistoriqueAction", "OneToMany", "1..*"),
        ("User → Notification", "OneToMany", "1..*"),
    ], caption="Tableau 2.5 : Relations et cardinalités du modèle de données")

    section_title(doc, "2.7 Machine d'états du dossier")
    P(doc, "Le dossier suit une machine d'états stricte implémentée dans la méthode "
      "changer_statut() du modèle. Chaque transition crée automatiquement un enregistrement "
      "HistoriqueAction pour la traçabilité :")
    T(doc, ["État", "Transitions possibles"], [
        ("BROUILLON", "→ EN_TRAITEMENT (soumission)"),
        ("EN_TRAITEMENT", "→ REJETE_AUTO | EN_ATTENTE | INCOMPLET | SUSPECT"),
        ("INCOMPLET", "→ EN_TRAITEMENT (complétion)"),
        ("SUSPECT", "→ EN_ATTENTE | REJETE_FINAL (décision manuelle)"),
        ("EN_ATTENTE", "→ PRESELECTIONNE | REJETE_FINAL"),
        ("PRESELECTIONNE", "→ ADMIS_FINAL | RECALE_FINAL | ABSENT_ECRIT"),
    ], caption="Tableau 2.6 : Machine d'états du dossier de candidature")

    section_title(doc, "2.8 Conclusion")
    P(doc, "Ce chapitre a détaillé l'architecture Full-Stack de la plateforme et le modèle "
      "de données relationnel complet. L'organisation modulaire en 5 applications Django assure "
      "une séparation claire des responsabilités. Le chapitre suivant présentera la logique métier "
      "et les algorithmes de scoring et d'OCR.")
    PB(doc)
