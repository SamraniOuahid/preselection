"""Chapitre IV : Conception de la solution."""
from report_utils import *

def add_ch4(doc):
    doc.add_heading("Chapitre IV : Conception de la solution",level=1)
    doc.add_heading("IV.1 Introduction",level=2)
    P(doc,"Ce chapitre présente la conception détaillée de la solution, incluant l'architecture technique, les diagrammes UML et le modèle de données.")

    doc.add_heading("IV.2 Méthodologie de conception",level=2)
    doc.add_heading("IV.2.1 Approche adoptée",level=3)
    P(doc,"Nous avons adopté une approche agile itérative, organisée en sprints hebdomadaires sur 4 semaines. Chaque sprint produit un incrément fonctionnel testé et validé avec l'encadrant.")
    doc.add_heading("IV.2.2 Choix du formalisme UML",level=3)
    P(doc,"Le formalisme UML 2.5 a été retenu pour la modélisation. Les diagrammes réalisés : cas d'utilisation, classes, séquence, activité, états-transitions.")

    doc.add_heading("IV.3 Architecture générale",level=2)
    doc.add_heading("IV.3.1 Vue d'ensemble",level=3)
    P(doc,"L'application suit une architecture Client-Serveur à trois niveaux : un frontend React (SPA), une API REST Django, et une base PostgreSQL. Les communications temps réel transitent par WebSocket via Django Channels et Redis.")
    FIG(doc,"Figure IV.1 : Architecture générale de l'application")
    doc.add_heading("IV.3.2 Architecture Client-Serveur REST",level=3)
    P(doc,"Le frontend communique avec le backend exclusivement via des endpoints REST sécurisés par JWT. Les réponses sont au format JSON. Le pattern est strictement stateless côté serveur, à l'exception des connexions WebSocket.")

    doc.add_heading("IV.4 Architecture technique détaillée",level=2)
    doc.add_heading("IV.4.1 Couche Frontend (React)",level=3)
    T(doc,["Composant","Rôle"],[("Pages","Vues principales (Landing, Auth, Candidat, Responsable, Admin)"),("Components","Composants réutilisables (formulaires, tableaux, badges)"),("Hooks","Logique métier React (useAuth, useNotifications)"),("Context","État global (AuthContext)"),("API","Module Axios centralisé pour les appels REST")])
    doc.add_heading("IV.4.2 Couche Backend (Django REST Framework)",level=3)
    T(doc,["App Django","Responsabilité"],[("users","Authentification, gestion des comptes, profils candidats"),("candidatures","Dossiers, documents, notes semestrielles"),("administration","Filières, diplômes acceptés, épreuves, historique"),("scoring","Règles de rejet, configuration scoring"),("notifications","Notifications email et WebSocket")])
    doc.add_heading("IV.4.3 Couche Services métier",level=3)
    T(doc,["Service","Fichier","Rôle"],[("Extraction","extraction.py","Extraction OCR des informations depuis les documents"),("Fuzzy Matching","fuzzy_matching.py","Correspondance floue des matières pour le scoring"),("Règles de rejet","regles.py","Application des règles de rejet automatique"),("Scoring","scoring.py","Calcul du score pondéré par filière"),("Vérification","verification_document.py","Vérification d'authenticité des documents"),("Invitation PDF","invitation_pdf.py","Génération des convocations PDF")])
    doc.add_heading("IV.4.4 Couche Base de données (PostgreSQL)",level=3)
    P(doc,"PostgreSQL 15 assure le stockage relationnel avec support des types JSON, UUID natif et transactions ACID. Les migrations sont gérées par le ORM Django.")
    doc.add_heading("IV.4.5 Couche Notifications",level=3)
    P(doc,"Les notifications combinent deux canaux : SMTP (Gmail App Password) pour les emails et Django Channels avec Redis pour les notifications WebSocket temps réel avec barre de progression.")
    doc.add_heading("IV.4.6 Couche Stockage fichiers",level=3)
    P(doc,"Les documents uploadés sont stockés dans le répertoire media/ organisé par dossier : media/dossiers/{uuid}/{filename}. Chaque fichier est associé à un enregistrement Document en base.")

    doc.add_heading("IV.5 Diagramme de classes",level=2)
    doc.add_heading("IV.5.1 Classes principales",level=3)
    T(doc,["Classe","Attributs clés","Responsabilité"],[
        ("User","email, cin, role, is_active","Authentification et autorisation"),
        ("Candidat","nom, prenom, telephone, date_naissance","Profil candidat"),
        ("Filiere","nom, code, niveau, places_disponibles","Configuration filière"),
        ("Dossier","statut, score, score_final, rang_final, mention","Candidature complète"),
        ("Document","type_doc, fichier, qualite_ocr","Pièce justificative"),
        ("NoteSemestre","semestre, moyenne, session, mention","Note semestrielle LMD"),
        ("RegleRejet","type_regle, parametre, is_active","Règle de rejet configurable"),
        ("ConfigScoring","matiere, poids, bonus_mention","Pondération scoring"),
        ("EpreuveEcrite","nom, date_epreuve, seuil_admission","Épreuve écrite"),
        ("NoteEcrite","note, resultat, rang_final","Note individuelle épreuve"),
        ("Notification","type_notif, sujet, statut, lue","Notification candidat"),
        ("HistoriqueAction","action, commentaire, timestamp","Traçabilité"),
    ])
    FIG(doc,"Figure IV.2 : Diagramme de classes principal")
    doc.add_heading("IV.5.2 Relations et cardinalités",level=3)
    T(doc,["Relation","Cardinalité"],[("User → Candidat","1..1"),("Candidat → Dossier","1..*"),("Dossier → Document","1..4"),("Dossier → NoteSemestre","1..6"),("Filiere → Dossier","1..*"),("Filiere → RegleRejet","1..*"),("Filiere → EpreuveEcrite","1..*"),("EpreuveEcrite → NoteEcrite","1..*"),("Dossier → HistoriqueAction","1..*"),("User → Notification","1..*")])

    doc.add_heading("IV.6 Diagrammes de séquence",level=2)
    for code,titre,desc in [
        ("DS01","Inscription et connexion","Le candidat s'inscrit avec email/CIN, reçoit un token JWT, puis accède à son espace."),
        ("DS02","Soumission et traitement automatique","Le candidat soumet → le backend lance la vérification OCR → applique les règles de rejet → calcule le score → met à jour le statut."),
        ("DS03","Validation par le responsable","Le responsable consulte un dossier, vérifie les alertes, puis valide ou rejette avec commentaire."),
        ("DS04","Import notes Excel et classement final","Le responsable uploade l'Excel → le wizard mappe les colonnes → les notes sont importées → le classement final est calculé (40% dossier + 60% épreuve)."),
        ("DS05","Notifications en masse via WebSocket","Le responsable sélectionne les destinataires → le backend envoie les emails SMTP en batch → notifie en temps réel via WebSocket avec progression."),
    ]:
        doc.add_heading(f"IV.6.{['DS01','DS02','DS03','DS04','DS05'].index(code)+1} {code} — {titre}",level=3)
        P(doc,desc)
        FIG(doc,f"Figure IV.{3+['DS01','DS02','DS03','DS04','DS05'].index(code)} : Diagramme de séquence — {titre}")

    doc.add_heading("IV.7 Diagrammes d'activité",level=2)
    doc.add_heading("IV.7.1 DA01 — Cycle de vie d'un dossier",level=3)
    P(doc,"Ce diagramme illustre les différentes activités depuis la création d'un dossier en brouillon jusqu'à la décision finale (admis ou recalé), en passant par la soumission, le traitement automatique et la validation manuelle.")
    FIG(doc,"Figure IV.8 : Diagramme d'activité — Cycle de vie d'un dossier")
    doc.add_heading("IV.7.2 DA02 — Processus de présélection de bout en bout",level=3)
    P(doc,"Ce diagramme modélise le processus complet depuis l'ouverture des candidatures jusqu'à la publication des résultats finaux, incluant les activités parallèles de traitement des dossiers et d'organisation de l'épreuve écrite.")
    FIG(doc,"Figure IV.9 : Diagramme d'activité — Processus complet")

    doc.add_heading("IV.8 Diagramme d'états-transitions",level=2)
    doc.add_heading("IV.8.1 Machine d'états du dossier",level=3)
    P(doc,"Le dossier suit une machine d'états stricte avec les transitions suivantes :")
    T(doc,["État","Transitions possibles"],[
        ("BROUILLON","→ EN_TRAITEMENT (soumission)"),
        ("EN_TRAITEMENT","→ REJETE_AUTO | EN_ATTENTE | INCOMPLET | SUSPECT"),
        ("INCOMPLET","→ EN_TRAITEMENT (complétion)"),
        ("SUSPECT","→ EN_ATTENTE | REJETE_FINAL (décision manuelle)"),
        ("EN_ATTENTE","→ PRESELECTIONNE | REJETE_FINAL"),
        ("PRESELECTIONNE","→ ADMIS_FINAL | RECALE_FINAL | ABSENT_ECRIT"),
    ])
    FIG(doc,"Figure IV.10 : Diagramme d'états-transitions du dossier")

    doc.add_heading("IV.9 Modèle de données",level=2)
    doc.add_heading("IV.9.1 Modèle Conceptuel de Données (MCD)",level=3)
    P(doc,"Le MCD identifie 12 entités principales et leurs associations. Les entités centrales sont User, Candidat, Dossier et Filiere, autour desquelles gravitent les entités de support (Document, NoteSemestre, NoteEcrite, etc.).")
    FIG(doc,"Figure IV.11 : Modèle Conceptuel de Données")
    doc.add_heading("IV.9.2 Modèle Logique de Données (MLD)",level=3)
    P(doc,"Le MLD traduit le MCD en schéma relationnel avec clés primaires (UUID), clés étrangères et contraintes d'unicité. Chaque entité correspond à une table PostgreSQL.")
    doc.add_heading("IV.9.3 Modèle Physique de Données (MPD)",level=3)
    P(doc,"Le MPD est implémenté via les migrations Django. Les tables principales : users, candidats, filieres, dossiers, documents, notes_semestres, regles_rejet, config_scoring, epreuves_ecrites, notes_ecrites, notifications, historique_actions.")

    doc.add_heading("IV.10 Dictionnaire de données",level=2)
    entities = [
        ("User",["id (UUID, PK)","email (VARCHAR, UNIQUE)","cin (VARCHAR, UNIQUE)","role (ENUM: CANDIDAT/RESPONSABLE/ADMIN)","is_active (BOOLEAN)","password (VARCHAR, hashed)"]),
        ("Candidat",["id (UUID, PK)","user_id (FK → User)","nom (VARCHAR)","prenom (VARCHAR)","telephone (VARCHAR)","date_naissance (DATE)"]),
        ("Filiere",["id (UUID, PK)","nom (VARCHAR)","code (VARCHAR, UNIQUE)","niveau (ENUM: BAC2/BAC3)","places_disponibles (INT)","date_ouverture/fermeture (DATETIME)"]),
        ("Dossier",["id (UUID, PK)","candidat_id (FK → Candidat)","filiere_id (FK → Filiere)","statut (ENUM, 11 valeurs)","score (DECIMAL)","score_final (DECIMAL)","rang_final (INT)","mention (ENUM)","moyenne_generale (DECIMAL)"]),
        ("Document",["id (UUID, PK)","dossier_id (FK → Dossier)","type_doc (ENUM)","fichier (FILE)","qualite_ocr (DECIMAL)","UNIQUE(dossier, type_doc)"]),
        ("NoteSemestre",["id (UUID, PK)","dossier_id (FK → Dossier)","semestre (ENUM: S1-S6)","moyenne (DECIMAL [10-20])","session (ENUM)","mention (ENUM, auto-calculé)"]),
        ("RegleRejet",["id (UUID, PK)","filiere_id (FK)","type_regle (ENUM, 7 types)","parametre (JSON)","is_active (BOOLEAN)","message_rejet (TEXT)"]),
        ("EpreuveEcrite",["id (UUID, PK)","filiere_id (FK)","nom (VARCHAR)","date_epreuve (DATE)","seuil_admission (DECIMAL)","statut (ENUM)"]),
        ("NoteEcrite",["id (UUID, PK)","epreuve_id (FK)","dossier_id (FK)","note (DECIMAL)","resultat (ENUM)","rang_final (INT)"]),
        ("Notification",["id (UUID, PK)","destinataire_id (FK → User)","type_notif (ENUM)","sujet (VARCHAR)","statut (ENUM)","lue (BOOLEAN)"]),
        ("HistoriqueAction",["id (UUID, PK)","dossier_id (FK)","acteur_id (FK → User)","action (ENUM)","commentaire (TEXT)","timestamp (DATETIME)"]),
    ]
    for i,(name,fields) in enumerate(entities):
        doc.add_heading(f"IV.10.{i+1} Entité {name}",level=3)
        rows = []
        for f in fields:
            if " (" in f:
                parts = f.split(" (", 1)
                rows.append((parts[0], parts[1].rstrip(")")))
            else:
                rows.append((f, ""))
        T(doc,["Attribut","Type / Contrainte"], rows)

    doc.add_heading("IV.11 Conclusion",level=2)
    P(doc,"La conception détaillée a permis de définir une architecture modulaire et extensible. Les diagrammes UML et le modèle de données constituent la base solide sur laquelle repose l'implémentation. Le chapitre suivant présentera les technologies choisies.")
    PB(doc)
