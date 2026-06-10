"""Chapitre III : Analyse et spécification des besoins."""
from report_utils import *

def add_ch3(doc):
    doc.add_heading("Chapitre III : Analyse et spécification des besoins",level=1)
    doc.add_heading("III.1 Introduction",level=2)
    P(doc,"Ce chapitre présente l'analyse détaillée des besoins fonctionnels et non fonctionnels de la plateforme, en partant de l'étude de l'existant et en identifiant les acteurs du système.")

    doc.add_heading("III.2 Étude de l'existant",level=2)
    doc.add_heading("III.2.1 Processus actuel de présélection",level=3)
    P(doc,"Le processus actuel repose sur la réception manuelle des dossiers (physiques ou email), la vérification des pièces par les agents, la saisie des notes dans Excel, le tri et classement manuel, puis la convocation à l'épreuve écrite.")
    doc.add_heading("III.2.2 Outils et supports utilisés",level=3)
    T(doc,["Outil","Usage"],[("Microsoft Excel","Saisie des notes et classement"),("Email","Communication avec les candidats"),("Papier","Réception et archivage des dossiers"),("Téléphone","Relances et réclamations")])
    doc.add_heading("III.2.3 Flux d'information actuel",level=3)
    P(doc,"Le flux actuel est linéaire et séquentiel : le candidat dépose son dossier → un agent vérifie les pièces → les notes sont saisies dans Excel → le responsable classe manuellement → les résultats sont communiqués par affichage ou email.")
    FIG(doc,"Figure III.1 : Flux d'information du processus actuel")

    doc.add_heading("III.3 Critique de l'existant",level=2)
    doc.add_heading("III.3.1 Points faibles identifiés",level=3)
    B(doc,["Processus lent et chronophage","Risque élevé d'erreurs de saisie","Absence de traçabilité des décisions","Pas de détection automatique des doublons","Classement sujet à des erreurs de calcul","Communication inefficace avec les candidats"])
    doc.add_heading("III.3.2 Tableau récapitulatif des problèmes",level=3)
    T(doc,["Problème","Conséquence","Priorité"],[("Saisie manuelle des notes","Erreurs de transcription","Haute"),("Pas de détection de doublons","Candidatures multiples non détectées","Haute"),("Classement Excel","Erreurs de formules, tri incorrect","Critique"),("Communication par email individuel","Retards, oublis de notification","Moyenne"),("Pas d'historique","Impossibilité d'audit","Haute")])

    doc.add_heading("III.4 Solution proposée",level=2)
    doc.add_heading("III.4.1 Vue d'ensemble de la solution",level=3)
    P(doc,"La solution proposée est une plateforme web Full Stack permettant la dématérialisation complète du processus de présélection. Elle offre un portail candidat pour le dépôt en ligne, un espace responsable pour le traitement et le suivi, et un espace administrateur pour la configuration.")
    doc.add_heading("III.4.2 Apports de la nouvelle plateforme",level=3)
    T(doc,["Processus actuel","Solution proposée"],[("Dépôt physique/email","Formulaire en ligne multi-étapes"),("Vérification manuelle","Vérification automatique des documents"),("Saisie Excel","Saisie intégrée + import Excel"),("Classement manuel","Scoring et classement automatique"),("Email individuel","Notifications en masse (WebSocket + SMTP)"),("Pas d'historique","Traçabilité complète des actions")])

    doc.add_heading("III.5 Identification des acteurs",level=2)
    T(doc,["Acteur","Description","Droits principaux"],[("Candidat","Personne postulant à une filière","Dépôt dossier, suivi, résultats"),("Responsable Scolarité","Agent gérant les candidatures","Traitement, validation, notifications"),("Administrateur","Gestionnaire de la plateforme","Configuration filières, règles, scoring"),("Système automatique","Agent logiciel","Vérification, scoring, rejet auto")])

    doc.add_heading("III.6 Besoins fonctionnels",level=2)
    doc.add_heading("III.6.1 Gestion des comptes et authentification",level=3)
    B(doc,["Inscription avec email et CIN (unique)","Connexion sécurisée par JWT (access + refresh token)","Trois rôles : Candidat, Responsable, Administrateur","Réinitialisation du mot de passe par email"])
    doc.add_heading("III.6.2 Dépôt et gestion des dossiers",level=3)
    B(doc,["Formulaire multi-étapes (5 étapes) avec sauvegarde brouillon","Sélection de la filière cible parmi les filières ouvertes","Saisie des informations académiques (diplôme, établissement, notes)","Saisie des notes semestrielles (S1 à S6) avec calcul automatique des mentions"])
    doc.add_heading("III.6.3 Vérification automatique des documents",level=3)
    B(doc,["Upload de 4 types de documents : Diplôme, Relevé de notes, CIN, Photo","Vérification du format et de la taille des fichiers","Extraction OCR des informations depuis les documents scannés","Score de confiance OCR pour chaque document"])
    doc.add_heading("III.6.4 Moteur de règles de rejet automatique",level=3)
    T(doc,["Règle","Description"],[("DIPLOME_INVALIDE","Diplôme non accepté pour la filière"),("MOYENNE_INSUFFISANTE","Moyenne générale en dessous du seuil"),("NOTE_ELIMINATOIRE","Note éliminatoire dans une matière clé"),("DOUBLON_CIN","CIN déjà utilisé dans un autre dossier"),("DOCUMENT_MANQUANT","Document obligatoire absent"),("DATE_INCOHERENTE","Incohérence dans les dates du diplôme"),("ETABLISSEMENT_INVALIDE","Établissement non reconnu")])
    doc.add_heading("III.6.5 Algorithme de scoring et classement",level=3)
    P(doc,"Le scoring repose sur une pondération configurable par filière. Chaque filière définit des coefficients par catégorie de matières. Le score final combine le score du dossier (40%) et la note de l'épreuve écrite (60%). Les mentions sont calculées automatiquement selon les seuils LMD.")
    doc.add_heading("III.6.6 Tableau de bord responsable",level=3)
    B(doc,["KPIs : nombre total de dossiers, taux de rejet, taux de présélection","Graphiques : répartition par statut, par filière, par mention","Filtres avancés : par statut, filière, date, score","Actions groupées : validation, rejet, notification en masse"])
    doc.add_heading("III.6.7 Gestion des épreuves écrites et import Excel",level=3)
    B(doc,["Création d'épreuves écrites par filière","Import des notes depuis un fichier Excel avec wizard de configuration","Mapping dynamique des colonnes Excel","Calcul automatique du classement final après import"])
    doc.add_heading("III.6.8 Système de notifications",level=3)
    B(doc,["Notifications temps réel via WebSocket (Django Channels)","Notifications par email via SMTP","Types : soumission, rejet, présélection, résultats","Historique des notifications avec statut d'envoi"])
    doc.add_heading("III.6.9 Export des résultats",level=3)
    P(doc,"Export des résultats en fichier Excel formaté avec classement, scores et statuts pour chaque filière.")

    doc.add_heading("III.7 Besoins non fonctionnels",level=2)
    T(doc,["Catégorie","Exigence"],[("Performance","Temps de réponse < 2s pour les opérations courantes"),("Sécurité","Authentification JWT, RBAC, protection CSRF/XSS"),("Disponibilité","Disponibilité 99.5% en période de candidatures"),("Maintenabilité","Code modulaire, documenté, architecture en couches"),("Utilisabilité","Interface responsive, intuitive, accessible")])

    doc.add_heading("III.8 Diagramme de cas d'utilisation global",level=2)
    P(doc,"Le diagramme de cas d'utilisation global présente les interactions entre les quatre acteurs identifiés et les principales fonctionnalités du système.")
    FIG(doc,"Figure III.2 : Diagramme de cas d'utilisation global")

    doc.add_heading("III.9 Description textuelle des cas d'utilisation",level=2)
    cus = [
        ("CU01","S'inscrire et se connecter","Candidat","Le candidat crée un compte avec email et CIN, puis se connecte via JWT.","Email et CIN valides","Compte créé, token JWT généré"),
        ("CU02","Déposer un dossier","Candidat","Le candidat remplit le formulaire multi-étapes et uploade ses documents.","Authentifié, filière ouverte","Dossier en statut BROUILLON"),
        ("CU03","Soumettre un dossier","Candidat","Le candidat soumet son dossier complet pour traitement.","Dossier complet","Statut → EN_TRAITEMENT"),
        ("CU04","Vérification automatique","Système","Le système vérifie les documents et applique les règles de rejet.","Dossier soumis","Score calculé, statut mis à jour"),
        ("CU05","Traiter les dossiers","Responsable","Le responsable consulte, valide ou rejette les dossiers.","Authentifié (rôle RESPONSABLE)","Décision enregistrée"),
        ("CU06","Configurer règles et scoring","Admin","L'admin configure les règles de rejet et les pondérations.","Authentifié (rôle ADMIN)","Configuration sauvegardée"),
        ("CU07","Importer notes Excel","Responsable","Import des notes d'épreuve écrite depuis un fichier Excel.","Épreuve créée, fichier valide","Notes importées, classement calculé"),
        ("CU08","Notifier les candidats","Responsable","Envoi de notifications en masse aux candidats.","Candidats sélectionnés","Notifications envoyées"),
        ("CU09","Consulter résultats","Candidat","Le candidat consulte l'état de son dossier et ses résultats.","Authentifié, dossier existant","Résultats affichés"),
    ]
    for code,nom,acteur,desc,pre,post in cus:
        doc.add_heading(f"III.9.{cus.index((code,nom,acteur,desc,pre,post))+1} {code} — {nom}",level=3)
        T(doc,["Champ","Valeur"],[(("Cas d'utilisation"),nom),("Acteur principal",acteur),("Description",desc),("Préconditions",pre),("Postconditions",post)])

    doc.add_heading("III.10 Conclusion",level=2)
    P(doc,"L'analyse des besoins a permis d'identifier clairement les fonctionnalités attendues et les contraintes du système. Les neuf cas d'utilisation définis couvrent l'ensemble du processus de présélection. Le chapitre suivant présentera la conception détaillée de la solution.")
    PB(doc)
