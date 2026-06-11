# Plateforme de Présélection - ENSA Béni Mellal

Ce projet est une plateforme complète pour la gestion de la présélection des candidats à l'ENSA Béni Mellal. Il est composé d'un backend en Django et d'un frontend en React, avec une architecture conteneurisée via Docker pour le déploiement en production.

## 🛠️ Technologies Utilisées

- **Backend** : Django, Django Rest Framework
- **Frontend** : React, Vite, Tailwind CSS
- **Base de données** : PostgreSQL (Production), SQLite (Développement local)
- **Cache & WebSockets** : Redis
- **Serveur Web & Reverse Proxy** : Nginx
- **Déploiement** : Docker, Docker Compose, Certbot (SSL)

---

## 🚀 Lancement en Local (Développement)

Pour travailler sur le projet en environnement de développement local, vous devez lancer le backend et le frontend séparément.

### 1. Démarrer le Backend (Django)

Ouvrez un terminal, placez-vous dans le répertoire du projet, et exécutez les commandes suivantes :

```bash
cd ensa-bm-preselection

# (Optionnel mais recommandé) Activer l'environnement virtuel
# source ../.venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations de base de données
python manage.py migrate

# Démarrer le serveur de développement
python manage.py runserver
```
L'API backend sera accessible à l'adresse : `http://127.0.0.1:8000`.

### 2. Démarrer le Frontend (React)

Ouvrez un **nouveau terminal**, placez-vous à la racine du projet et exécutez :

```bash
cd frontend

# Installer les dépendances Node
npm install

# Démarrer le serveur de développement frontend
npm run dev
```
L'interface de l'application sera accessible sur l'URL locale fournie par Vite (généralement `http://localhost:5173`).

---

## 🌍 Déploiement en Production (Serveur Ubuntu)

Le projet est conçu pour être déployé facilement sur un serveur physique ou VPS (idéalement Ubuntu 20.04 LTS ou supérieur) en utilisant un script automatisé.

### Étapes de déploiement automatique

1. Connectez-vous à votre serveur de production via SSH.
2. Clonez le dépôt Git du projet.
3. Exécutez le script d'installation avec les droits d'administrateur :

```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

**Ce que fait le script :**
- Installation de Docker et Docker Compose.
- Configuration interactive de l'environnement (domaine, base de données, SMTP, etc.) et création du fichier `.env`.
- Obtention d'un certificat SSL valide via Let's Encrypt (Certbot).
- Construction et lancement de l'ensemble des conteneurs via Docker Compose.
- Exécution automatique des migrations Django et collecte des fichiers statiques.
- Mise en place d'une tâche planifiée (cron) pour le renouvellement automatique du SSL.
- Configuration du pare-feu (UFW) pour autoriser les ports HTTP(80), HTTPS(443) et SSH(22).

### Commandes Docker utiles (Production)

Une fois le projet déployé (le répertoire par défaut est `/opt/ensa-preselection`), placez-vous dans ce dossier pour utiliser Docker Compose :

```bash
cd /opt/ensa-preselection

# Voir l'état des conteneurs en cours d'exécution
docker compose ps

# Voir et suivre les logs (pour tous les services ou un spécifique comme 'backend' ou 'nginx')
docker compose logs -f

# Redémarrer tous les services
docker compose restart

# Arrêter les conteneurs sans perdre les données
docker compose down

# Relancer les conteneurs (en arrière-plan)
docker compose up -d
```
