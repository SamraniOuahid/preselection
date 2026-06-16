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

### Déploiement automatique via script (Recommandé)

1. Connectez-vous à votre serveur de production via SSH.
2. Clonez le dépôt Git du projet.
3. Exécutez le script d'installation avec les droits d'administrateur :

```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

*(Ce script s'occupe de tout : installation de Docker, prompt interactif pour configurer le `.env`, obtention du certificat SSL Let's Encrypt, build des conteneurs, exécution des migrations et création du superutilisateur).*

---

### 🐳 Lancement manuel avec Docker (Première fois après un Clone)

Si vous venez de cloner le projet et que vous souhaitez le lancer manuellement avec Docker (sans passer par le script automatique ou pour des tests locaux), suivez ces étapes :

#### 1. Configurer l'environnement
Copiez le fichier d'exemple pour créer votre fichier de configuration `.env` :
```bash
cp .env.example .env
```
Ouvrez le fichier `.env` fraîchement créé et modifiez les valeurs nécessaires (notamment `SECRET_KEY`, les mots de passe de base de données, etc.).

#### 2. Lancer les conteneurs (Build)
Construisez et démarrez tous les services définis dans `docker-compose.yml` en arrière-plan :
```bash
docker compose up --build -d
```
*(Cela va télécharger les images nécessaires, compiler le frontend React, préparer Nginx, et lancer PostgreSQL, Redis et Django).*

#### 3. Effectuer les migrations de la base de données
Appliquez le schéma de base de données dans le conteneur PostgreSQL via le backend Django :
```bash
docker compose exec backend python manage.py migrate
```

#### 4. Collecter les fichiers statiques
Rassemblez tous les fichiers statiques du backend pour qu'ils soient servis par Nginx :
```bash
docker compose exec backend python manage.py collectstatic --noinput
```

#### 5. Créer un administrateur (Superuser)
Créez un compte administrateur pour accéder à l'interface Django Admin (`/admin`) :
```bash
docker compose exec backend python manage.py createsuperuser
```
Suivez les invites dans le terminal pour saisir le nom d'utilisateur, l'adresse email et le mot de passe.

---

### Commandes Docker utiles

Une fois le projet démarré, vous pouvez utiliser ces commandes :
```bash
# Voir l'état des conteneurs
docker compose ps

# Voir les logs en temps réel
docker compose logs -f

# Arrêter les conteneurs
docker compose down

# Relancer les conteneurs déjà construits
docker compose up -d
```
