# ---------------------------------------------------------------------------
# AI Financial Coach — frontend (React + Vite, served by nginx)
# Stage 1 builds the static bundle; stage 2 serves it on a tiny nginx image
# and reverse-proxies /api/* to the backend container.
# ---------------------------------------------------------------------------

# ---- Stage 1: build the static assets --------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

# Install deps from the lockfile for reproducible builds.
COPY package.json package-lock.json ./
RUN npm ci

# Build. VITE_API_URL is intentionally left empty so the app uses the
# relative "/api" base, which nginx proxies to the backend at runtime.
COPY . .
ENV VITE_API_URL=""
RUN npm run build

# ---- Stage 2: serve with nginx ---------------------------------------------
FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
