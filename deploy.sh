#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy.sh — Script de déploiement automatisé
# Plateforme de Présélection ENSA Béni Mellal
# Cible : Ubuntu Server 20.04 LTS (serveur physique)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Couleurs pour le terminal ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Configuration ─────────────────────────────────────────────────────────
REPO_URL="https://github.com/SamraniOuahid/preselection.git"
APP_DIR="/opt/ensa-preselection"
BRANCH="main"

# ── Fonctions utilitaires ─────────────────────────────────────────────────
log_info()    { echo -e "${BLUE}[INFO]${NC}    $1"; }
log_success() { echo -e "${GREEN}[✓]${NC}      $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $1"; }
log_error()   { echo -e "${RED}[✗]${NC}      $1"; }
log_step()    { echo -e "\n${CYAN}══════════════════════════════════════════════${NC}"; \
                echo -e "${CYAN}  $1${NC}"; \
                echo -e "${CYAN}══════════════════════════════════════════════${NC}\n"; }

# ── Vérification : exécution en root ──────────────────────────────────────
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root (sudo ./deploy.sh)"
        exit 1
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Installation de Docker Engine + Docker Compose v2
# ══════════════════════════════════════════════════════════════════════════
install_docker() {
    log_step "ÉTAPE 1 : Installation de Docker"

    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+')
        log_success "Docker déjà installé (v${DOCKER_VERSION})"
    else
        log_info "Installation de Docker Engine..."

        # Pré-requis
        apt-get update -qq
        apt-get install -y -qq \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # Clé GPG officielle Docker
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
            gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg

        # Dépôt Docker
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
          https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | \
          tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Installation
        apt-get update -qq
        apt-get install -y -qq \
            docker-ce \
            docker-ce-cli \
            containerd.io \
            docker-buildx-plugin \
            docker-compose-plugin

        # Démarrer et activer Docker
        systemctl enable --now docker

        log_success "Docker Engine installé avec succès"
    fi

    # Vérifier Docker Compose v2
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
        log_success "Docker Compose v2 disponible (v${COMPOSE_VERSION})"
    else
        log_error "Docker Compose v2 non disponible. Vérifiez l'installation."
        exit 1
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Clonage du dépôt Git
# ══════════════════════════════════════════════════════════════════════════
clone_repo() {
    log_step "ÉTAPE 2 : Clonage du dépôt Git"

    # Installer git si nécessaire
    if ! command -v git &> /dev/null; then
        log_info "Installation de Git..."
        apt-get install -y -qq git
    fi

    if [[ -d "$APP_DIR" ]]; then
        log_warn "Le répertoire $APP_DIR existe déjà"
        read -p "Voulez-vous le supprimer et re-cloner ? (o/N) : " -r
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            rm -rf "$APP_DIR"
            log_info "Ancien répertoire supprimé"
        else
            log_info "Mise à jour du dépôt existant..."
            cd "$APP_DIR"
            git fetch origin
            git reset --hard "origin/${BRANCH}"
            log_success "Dépôt mis à jour"
            return
        fi
    fi

    git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
    log_success "Dépôt cloné dans $APP_DIR"
    cd "$APP_DIR"
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Configuration du fichier .env
# ══════════════════════════════════════════════════════════════════════════
setup_env() {
    log_step "ÉTAPE 3 : Configuration de l'environnement"

    cd "$APP_DIR"

    if [[ -f .env ]]; then
        log_warn "Le fichier .env existe déjà"
        read -p "Voulez-vous le recréer ? (o/N) : " -r
        if [[ ! $REPLY =~ ^[Oo]$ ]]; then
            log_info "Conservation du .env existant"
            return
        fi
    fi

    # Copier le template
    cp .env.example .env
    log_info "Fichier .env créé depuis .env.example"

    # Générer une SECRET_KEY sécurisée
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || \
                 openssl rand -base64 50 | tr -dc 'a-zA-Z0-9' | head -c 64)
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    log_success "SECRET_KEY générée automatiquement"

    # Demander les informations interactivement
    echo ""
    read -p "Nom de domaine (ex: preselection.ensa-bm.ac.ma) : " DOMAIN
    read -p "Email pour Certbot/Let's Encrypt : " CERTBOT_EMAIL
    read -p "Mot de passe PostgreSQL : " -s DB_PASS
    echo ""
    read -p "Email SMTP (Gmail) : " SMTP_EMAIL
    read -p "Mot de passe d'application SMTP : " -s SMTP_PASS
    echo ""

    # Appliquer les valeurs
    sed -i "s|DOMAIN_NAME=.*|DOMAIN_NAME=${DOMAIN}|" .env
    sed -i "s|CERTBOT_EMAIL=.*|CERTBOT_EMAIL=${CERTBOT_EMAIL}|" .env
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN}|" .env
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=${DB_PASS}|" .env
    sed -i "s|EMAIL_HOST_USER=.*|EMAIL_HOST_USER=${SMTP_EMAIL}|" .env
    sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=${SMTP_PASS}|" .env

    log_success "Fichier .env configuré"
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Obtention du certificat SSL (Let's Encrypt)
# ══════════════════════════════════════════════════════════════════════════
setup_ssl() {
    log_step "ÉTAPE 4 : Configuration SSL / Let's Encrypt"

    cd "$APP_DIR"

    # Charger les variables d'environnement
    source <(grep -v '^#' .env | sed 's/^/export /')

    # Créer les répertoires nécessaires
    mkdir -p nginx/certbot/conf nginx/certbot/www

    # Vérifier si un certificat existe déjà
    if [[ -d "nginx/certbot/conf/live/${DOMAIN_NAME}" ]]; then
        log_success "Certificat SSL existant trouvé pour ${DOMAIN_NAME}"
        return
    fi

    log_info "Obtention d'un certificat SSL pour ${DOMAIN_NAME}..."

    # Créer une config Nginx temporaire (HTTP uniquement) pour le challenge ACME
    cat > nginx/default-init.conf << 'INITEOF'
server {
    listen 80;
    server_name _;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'ENSA BM - En cours de configuration...';
        add_header Content-Type text/plain;
    }
}
INITEOF

    # Lancer Nginx temporairement avec la config HTTP-only
    docker compose run --rm -d \
        -v "$(pwd)/nginx/default-init.conf:/etc/nginx/conf.d/default.conf:ro" \
        -v "$(pwd)/nginx/certbot/www:/var/www/certbot" \
        -p 80:80 \
        --name ensa_nginx_init \
        nginx:1.27-alpine || true

    # Petit délai pour que Nginx démarre
    sleep 3

    # Obtenir le certificat via Certbot
    docker run --rm \
        -v "$(pwd)/nginx/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/nginx/certbot/www:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "${CERTBOT_EMAIL}" \
        --agree-tos \
        --no-eff-email \
        -d "${DOMAIN_NAME}" \
        -d "www.${DOMAIN_NAME}"

    # Arrêter le Nginx temporaire
    docker stop ensa_nginx_init 2>/dev/null || true

    # Nettoyer le fichier temporaire
    rm -f nginx/default-init.conf

    if [[ -d "nginx/certbot/conf/live/${DOMAIN_NAME}" ]]; then
        log_success "Certificat SSL obtenu avec succès !"
    else
        log_warn "Échec de l'obtention du certificat SSL."
        log_warn "Vous pouvez réessayer manuellement après le déploiement."
        log_info "Création d'un certificat auto-signé temporaire..."

        # Créer un certificat auto-signé comme fallback
        mkdir -p "nginx/certbot/conf/live/${DOMAIN_NAME}"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "nginx/certbot/conf/live/${DOMAIN_NAME}/privkey.pem" \
            -out "nginx/certbot/conf/live/${DOMAIN_NAME}/fullchain.pem" \
            -subj "/CN=${DOMAIN_NAME}" 2>/dev/null
        log_success "Certificat auto-signé créé (remplacez-le par Let's Encrypt)"
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Build et lancement des conteneurs
# ══════════════════════════════════════════════════════════════════════════
build_and_start() {
    log_step "ÉTAPE 5 : Build et lancement des conteneurs"

    cd "$APP_DIR"

    # Arrêter les conteneurs existants
    docker compose down --remove-orphans 2>/dev/null || true

    # Builder et démarrer
    log_info "Build des images Docker (cela peut prendre quelques minutes)..."
    docker compose up --build -d

    # Attendre que les services soient prêts
    log_info "Attente du démarrage des services..."
    sleep 10

    # Vérifier l'état des conteneurs
    echo ""
    docker compose ps
    echo ""

    log_success "Tous les conteneurs sont lancés"
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Migrations Django
# ══════════════════════════════════════════════════════════════════════════
run_migrations() {
    log_step "ÉTAPE 6 : Migrations Django"

    cd "$APP_DIR"

    log_info "Application des migrations..."
    docker compose exec -T backend python manage.py migrate --noinput

    log_info "Collecte des fichiers statiques..."
    docker compose exec -T backend python manage.py collectstatic --noinput

    log_success "Migrations appliquées avec succès"

    # Créer un superuser si nécessaire
    echo ""
    read -p "Voulez-vous créer un superuser Django ? (o/N) : " -r
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        docker compose exec backend python manage.py createsuperuser
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 7 : Configuration du renouvellement SSL automatique
# ══════════════════════════════════════════════════════════════════════════
setup_ssl_renewal() {
    log_step "ÉTAPE 7 : Renouvellement automatique SSL"

    cd "$APP_DIR"

    # Créer le script de renouvellement
    cat > /opt/ensa-renew-ssl.sh << 'RENEWEOF'
#!/usr/bin/env bash
# Renouvellement automatique du certificat SSL Let's Encrypt
cd /opt/ensa-preselection
docker compose run --rm certbot certbot renew --quiet
docker compose exec -T nginx nginx -s reload
RENEWEOF

    chmod +x /opt/ensa-renew-ssl.sh

    # Ajouter un cron job (2x par jour comme recommandé par Let's Encrypt)
    CRON_JOB="0 2,14 * * * /opt/ensa-renew-ssl.sh >> /var/log/ensa-ssl-renew.log 2>&1"

    # Vérifier si le cron existe déjà
    if crontab -l 2>/dev/null | grep -q "ensa-renew-ssl"; then
        log_warn "Cron de renouvellement SSL déjà configuré"
    else
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        log_success "Cron de renouvellement SSL configuré (2x/jour à 2h et 14h)"
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 8 : Configuration du firewall (UFW)
# ══════════════════════════════════════════════════════════════════════════
setup_firewall() {
    log_step "ÉTAPE 8 : Configuration du Firewall (UFW)"

    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp    # SSH
        ufw allow 80/tcp    # HTTP
        ufw allow 443/tcp   # HTTPS
        ufw --force enable
        log_success "Firewall configuré (SSH + HTTP + HTTPS)"
    else
        log_warn "UFW non installé, configuration du firewall ignorée"
    fi
}

# ══════════════════════════════════════════════════════════════════════════
# Résumé final
# ══════════════════════════════════════════════════════════════════════════
print_summary() {
    source <(grep -v '^#' "$APP_DIR/.env" | sed 's/^/export /')

    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  🌐 Site web:        ${CYAN}https://${DOMAIN_NAME}${NC}"
    echo -e "  🔧 API Django:      ${CYAN}https://${DOMAIN_NAME}/api/${NC}"
    echo -e "  👤 Django Admin:    ${CYAN}https://${DOMAIN_NAME}/admin/${NC}"
    echo ""
    echo -e "  📁 Répertoire:      ${APP_DIR}"
    echo -e "  📋 Logs backend:    docker compose -f ${APP_DIR}/docker-compose.yml logs backend"
    echo -e "  📋 Logs nginx:      docker compose -f ${APP_DIR}/docker-compose.yml logs nginx"
    echo ""
    echo -e "  ${YELLOW}Commandes utiles :${NC}"
    echo -e "    cd ${APP_DIR}"
    echo -e "    docker compose ps          # État des conteneurs"
    echo -e "    docker compose logs -f     # Suivre les logs"
    echo -e "    docker compose restart     # Redémarrer"
    echo -e "    docker compose down        # Arrêter"
    echo -e "    docker compose up -d       # Relancer"
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════
# Main — Orchestration du déploiement complet
# ══════════════════════════════════════════════════════════════════════════
main() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║   🎓 ENSA Béni Mellal — Plateforme de Présélection       ║"
    echo "║   Script de déploiement automatisé                       ║"
    echo "║   Cible : Ubuntu Server 20.04 LTS                        ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_root
    install_docker
    clone_repo
    setup_env
    setup_ssl
    build_and_start
    run_migrations
    setup_ssl_renewal
    setup_firewall
    print_summary
}

main "$@"
