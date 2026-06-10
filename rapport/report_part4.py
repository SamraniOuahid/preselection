"""Chapitres V et VI : Technologies + Réalisation."""
from report_utils import *

def add_ch5(doc):
    doc.add_heading("Chapitre V : Technologies et environnement de développement",level=1)
    doc.add_heading("V.1 Introduction",level=2)
    P(doc,"Ce chapitre décrit les technologies, frameworks et outils utilisés pour le développement de la plateforme, ainsi que la justification des choix techniques.")

    doc.add_heading("V.2 Langages de programmation",level=2)
    T(doc,["Langage","Version","Usage"],[("Python","3.10","Backend Django, scripts, services métier"),("JavaScript","ES2022","Frontend React, logique interactive"),("HTML5 / CSS3","—","Structure et mise en forme des interfaces")])

    doc.add_heading("V.3 Frameworks et bibliothèques",level=2)
    T(doc,["Technologie","Version","Rôle"],[
        ("Django","4.2 LTS","Framework backend principal"),
        ("Django REST Framework","3.17","Construction de l'API REST"),
        ("Django Channels","4.0","WebSockets temps réel"),
        ("SimpleJWT","5.5","Authentification par tokens JWT"),
        ("React","18","Framework frontend SPA"),
        ("Tailwind CSS","3.x","Framework CSS utilitaire"),
        ("React Router","v6","Navigation SPA côté client"),
        ("Axios","1.x","Client HTTP pour appels API"),
        ("Recharts","2.x","Graphiques et visualisations"),
        ("React Hook Form + Zod","—","Gestion et validation des formulaires"),
        ("pdfplumber + pytesseract","—","Extraction OCR des documents PDF"),
        ("openpyxl / reportlab","—","Import/Export Excel et génération PDF"),
        ("fuzzywuzzy","0.18","Correspondance floue des matières"),
    ])

    doc.add_heading("V.4 Base de données",level=2)
    T(doc,["Technologie","Rôle"],[("PostgreSQL 15","Base de données relationnelle principale"),("Redis","Channel Layer pour WebSocket (Django Channels)")])

    doc.add_heading("V.5 Outils de développement",level=2)
    T(doc,["Outil","Usage"],[("Visual Studio Code","IDE principal"),("Antigravity AI","Agent IA de développement assisté"),("Git / GitHub","Gestion de versions et collaboration"),("Postman","Tests manuels des endpoints API"),("draw.io / PlantUML","Modélisation UML"),("Vite","Bundler et serveur de développement frontend")])

    doc.add_heading("V.6 Justification des choix techniques",level=2)
    doc.add_heading("V.6.1 Pourquoi Django plutôt que Node.js",level=3)
    P(doc,"Django offre un ORM mature, un système d'administration intégré, une gestion native des migrations et une sécurité robuste (CSRF, XSS). Son écosystème Python facilite l'intégration des bibliothèques OCR (pytesseract, pdfplumber) et de traitement de données.")
    doc.add_heading("V.6.2 Pourquoi React plutôt que Vue.js",level=3)
    P(doc,"React bénéficie d'un écosystème plus riche, d'une communauté plus large et d'une meilleure intégration avec les outils de test. Son modèle de composants fonctionnels avec hooks offre une flexibilité optimale pour les interfaces complexes.")
    doc.add_heading("V.6.3 Pourquoi PostgreSQL plutôt que MySQL",level=3)
    P(doc,"PostgreSQL offre un support natif des types JSON et UUID, des performances supérieures pour les requêtes complexes, et une meilleure conformité au standard SQL. Il est le choix recommandé par Django.")
    doc.add_heading("V.6.4 Pourquoi WebSocket pour les notifications",level=3)
    P(doc,"Les WebSockets permettent une communication bidirectionnelle en temps réel, essentielle pour afficher la progression des notifications en masse et mettre à jour les statuts des dossiers instantanément sans polling.")

    doc.add_heading("V.7 Environnement matériel et logiciel",level=2)
    T(doc,["Composant","Spécification"],[("Machine","Dell Latitude 7480"),("OS","Ubuntu 24.04 LTS"),("RAM","16 Go"),("Processeur","Intel Core i7"),("Stockage","256 Go SSD"),("Python","3.10.12"),("Node.js","20.x LTS"),("PostgreSQL","15.x"),("Redis","7.x")])

    doc.add_heading("V.8 Conclusion",level=2)
    P(doc,"Les choix technologiques reposent sur des critères de maturité, performance, sécurité et adéquation avec les besoins du projet. Cette stack moderne garantit maintenabilité et évolutivité.")
    PB(doc)

def add_ch6(doc):
    doc.add_heading("Chapitre VI : Réalisation de l'application",level=1)
    doc.add_heading("VI.1 Introduction",level=2)
    P(doc,"Ce chapitre présente la réalisation concrète de l'application : structure du projet, interfaces développées, fonctionnalités implémentées, règles métier, sécurité et difficultés rencontrées.")

    doc.add_heading("VI.2 Structure du projet",level=2)
    doc.add_heading("VI.2.1 Architecture Backend (5 apps Django)",level=3)
    P(doc,"Le backend est organisé en 5 applications Django indépendantes et cohésives :")
    T(doc,["Application","Fichiers clés","Lignes de code (approx.)"],[("users","models.py, serializers.py, views.py","~500"),("candidatures","models.py, views.py, services/","~2500"),("administration","models.py, views.py","~1200"),("scoring","models.py, views.py","~400"),("notifications","models.py, consumers.py, views.py","~600")])
    P(doc,"Le répertoire candidatures/services/ contient la logique métier critique : extraction OCR, fuzzy matching, règles de rejet, scoring et vérification de documents.")

    doc.add_heading("VI.2.2 Architecture Frontend",level=3)
    T(doc,["Répertoire","Contenu"],[("src/pages/","Pages par rôle (auth, candidat, responsable, admin)"),("src/components/","Composants réutilisables (layout, notifications, formulaires)"),("src/hooks/","Hooks personnalisés (useAuth, useNotifications)"),("src/api/","Module Axios centralisé"),("src/context/","Contexte global (AuthContext)"),("src/utils/","Fonctions utilitaires (mentions, formatage)")])

    doc.add_heading("VI.3 Interfaces réalisées",level=2)
    interfaces = [
        ("VI.3.1","Page d'accueil","Landing page responsive avec présentation de l'ENSA BM, statistiques en chiffres, filières proposées et appel à l'action pour les candidats."),
        ("VI.3.2","Authentification","Pages d'inscription (email + CIN) et connexion avec validation en temps réel, gestion des erreurs et redirection selon le rôle."),
        ("VI.3.3","Formulaire de candidature (5 étapes)","Étape 1 : Informations personnelles. Étape 2 : Parcours académique et diplôme. Étape 3 : Notes semestrielles (S1-S6) avec calcul automatique des mentions. Étape 4 : Upload des documents. Étape 5 : Récapitulatif et soumission."),
        ("VI.3.4","Suivi de dossier","Interface temps réel affichant le statut du dossier avec badge coloré, historique des actions et notifications reçues."),
        ("VI.3.5","Résultats épreuve écrite","Affichage de la note obtenue, du rang et du résultat (Admis/Recalé/Absent) avec détails de l'épreuve."),
        ("VI.3.6","Dashboard responsable","Tableau de bord avec KPIs (total dossiers, taux de rejet, présélectionnés), graphiques Recharts (répartition par statut et filière), accès rapide aux actions."),
        ("VI.3.7","Gestion des dossiers","Liste paginée avec filtres (statut, filière, recherche), tri par score, actions de validation/rejet avec commentaire."),
        ("VI.3.8","Détail d'un dossier","Vue complète du dossier : informations candidat, notes, documents uploadés, score, historique des actions, alertes de vérification."),
        ("VI.3.9","Configuration admin","Interface de configuration des filières, diplômes acceptés, règles de rejet et pondérations de scoring."),
        ("VI.3.10","Épreuves écrites et import Excel","Wizard d'import en 3 étapes : upload du fichier → mapping des colonnes → prévisualisation et confirmation. Calcul automatique du classement."),
        ("VI.3.11","Notifications","Icône cloche avec badge de compteur, panneau déroulant avec historique, marquage lu/non-lu."),
    ]
    for num,titre,desc in interfaces:
        doc.add_heading(f"{num} Interface — {titre}",level=3)
        P(doc,desc)
        FIG(doc,f"Figure VI.{interfaces.index((num,titre,desc))+1} : {titre}")

    doc.add_heading("VI.4 Fonctionnalités développées",level=2)
    foncs = [
        ("VI.4.1","Authentification JWT et rôles","Système complet avec access/refresh tokens, middleware de vérification, décorateurs de permissions (@permission_classes) et RBAC à 3 niveaux."),
        ("VI.4.2","Formulaire multi-étapes","Formulaire React avec React Hook Form et Zod, sauvegarde brouillon automatique, validation dynamique des notes par semestre (plage 10-20)."),
        ("VI.4.3","Upload et traitement documents","Upload sécurisé avec validation MIME type, stockage organisé par UUID de dossier, extraction OCR via pdfplumber et pytesseract."),
        ("VI.4.4","Moteur de règles de rejet","7 types de règles configurables par filière, exécution séquentielle avec court-circuit, journalisation des motifs de rejet."),
        ("VI.4.5","Scoring et classement","Algorithme de scoring pondéré par catégorie de matières via fuzzy matching, bonus mention, coefficient par type de diplôme, classement par filière."),
        ("VI.4.6","Import Excel avec wizard","Upload, détection automatique des colonnes, mapping interactif, prévisualisation, import batch avec calcul du classement final."),
        ("VI.4.7","Notifications WebSocket","Django Channels avec Redis, envoi batch SMTP avec progression temps réel, historique persisté en base."),
        ("VI.4.8","Export Excel formaté","Export des résultats par filière avec openpyxl : classement, scores, statuts, mise en forme conditionnelle."),
    ]
    for num,titre,desc in foncs:
        doc.add_heading(f"{num} {titre}",level=3)
        P(doc,desc)

    doc.add_heading("VI.5 Règles métier implémentées",level=2)
    doc.add_heading("VI.5.1 Validation des notes (système LMD)",level=3)
    P(doc,"Les moyennes semestrielles sont strictement validées dans la plage [10.00, 20.00]. Le backend applique cette validation dans la méthode clean() du modèle NoteSemestre et le frontend l'impose via les validateurs Zod.")
    doc.add_heading("VI.5.2 Calcul automatique des mentions",level=3)
    T(doc,["Plage","Mention"],[("≥ 16.00","Très Bien"),("≥ 14.00","Bien"),("≥ 12.00","Assez Bien"),("≥ 10.00","Passable")])
    P(doc,"La mention est calculée automatiquement dans la méthode save() du modèle et verrouillée (editable=False).")
    doc.add_heading("VI.5.3 Machine d'états du dossier",level=3)
    P(doc,"La méthode changer_statut() du modèle Dossier gère les transitions d'état de façon contrôlée, crée un enregistrement HistoriqueAction pour chaque changement et met à jour la date de soumission si nécessaire.")
    doc.add_heading("VI.5.4 Formule de score final",level=3)
    P(doc,"Score_final = (Score_dossier × 0.40) + (Note_épreuve_normalisée × 0.60). Le score du dossier intègre les moyennes pondérées par catégorie de matières et les bonus de mention/diplôme.")
    doc.add_heading("VI.5.5 Gestion des égalités",level=3)
    P(doc,"En cas d'égalité de score final, le département est fait par : (1) la note d'épreuve écrite, (2) la moyenne générale du dossier, (3) la date de soumission (premier arrivé, premier servi).")

    doc.add_heading("VI.6 Gestion des erreurs",level=2)
    T(doc,["Couche","Mécanisme"],[("Backend","Exceptions Django personnalisées, try/catch dans les services, codes HTTP appropriés (400, 401, 403, 404, 500)"),("Frontend","États error/loading dans les composants, intercepteur Axios pour le refresh token, messages d'erreur utilisateur"),("SMTP","Gestion des erreurs d'envoi avec statut ECHEC et message d'erreur persisté dans le modèle Notification")])

    doc.add_heading("VI.7 Sécurité de l'application",level=2)
    T(doc,["Mesure","Implémentation"],[("Authentification","JWT (access 15min + refresh 24h)"),("Autorisation","RBAC à 3 niveaux via @permission_classes"),("CSRF","Protection Django middleware activée"),("XSS","Échappement automatique des templates Django + React"),("Injection SQL","ORM Django avec requêtes paramétrées"),("Filtrage données","Serializers Django filtrant les champs selon le rôle"),("Logs sécurisés","Fichier ensa_presel.log avec rotation"),("Confidentialité","Scores OCR et détails internes masqués côté candidat")])

    doc.add_heading("VI.8 Difficultés rencontrées et solutions",level=2)
    T(doc,["Difficulté","Solution apportée"],[("WebSocket + JWT expiré","Middleware d'authentification WebSocket avec refresh automatique du token"),("SMTP Gmail","Configuration App Password avec gestion des erreurs de connexion"),("Imports circulaires Django","Import local dans les méthodes (from X import Y) au lieu d'imports globaux"),("OCR faible qualité","Système de fallback sur moyenne générale avec flag de vérification manuelle"),("Ordre des migrations","Dépendances explicites dans les fichiers de migration")])

    doc.add_heading("VI.9 Conclusion",level=2)
    P(doc,"La réalisation a couvert l'ensemble des fonctionnalités spécifiées. L'application offre une expérience utilisateur fluide et professionnelle, avec une sécurité robuste et une gestion des erreurs complète. Le chapitre suivant présentera la stratégie de tests.")
    PB(doc)
