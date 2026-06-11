# ──────────────────────────────────────────────────────────────────────
# Dockerfile — Frontend React (Multi-stage: Build + Nginx)
# ──────────────────────────────────────────────────────────────────────

# ── Stage 1: Build the React app ─────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files first (Docker layer caching)
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config (will be mounted via docker-compose instead)
# The nginx config is handled at the docker-compose level

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
