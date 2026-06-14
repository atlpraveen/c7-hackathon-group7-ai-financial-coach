# 🐳 Running the AI Financial Coach with Docker

This guide takes you from a clean machine to a fully running app using **only
Docker**. No Python, Node, Postgres, or Qdrant need to be installed on the host
— every component runs in a container.

The stack that comes up:

| Container  | Image / build        | Role                                            | Host port |
|------------|----------------------|-------------------------------------------------|-----------|
| `frontend` | built (nginx + SPA)  | Serves the React UI, proxies `/api/*` → backend | **5173**  |
| `backend`  | built (FastAPI)      | REST API + multi-agent engine                   | **8000**  |
| `db`       | `postgres:16-alpine` | Persistent analytics + multi-user data          | _internal_|
| `qdrant`   | `qdrant/qdrant`      | Vector search for document RAG                   | _internal_|

> **Everything is optional except Docker.** With no API keys the app still runs
> end-to-end (deterministic reasoning + Postgres + Qdrant). Adding an
> `OPENROUTER_API_KEY` lights up LLM routing, narration, AI categorization, and
> streaming automatically.

---

## 1. Install Docker

You need **Docker Engine 20.10+** with the **Compose v2 plugin** (`docker
compose`, not the old `docker-compose`).

### macOS
1. Download **Docker Desktop** from <https://www.docker.com/products/docker-desktop/>.
2. Open the `.dmg`, drag Docker to *Applications*, launch it, and wait for the
   whale icon in the menu bar to say *“Docker Desktop is running”*.

### Windows
1. Install **Docker Desktop** (enable the WSL 2 backend when prompted).
2. Launch Docker Desktop and wait until it reports it is running.
3. Run the commands below from **PowerShell** or a **WSL** shell.

### Linux
```bash
# Docker Engine + Compose plugin (Debian/Ubuntu)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"   # then log out/in so you can run docker without sudo
```

### Verify the install
```bash
docker --version
docker compose version
```
Both commands should print a version. If `docker compose version` fails, your
Docker is too old — update Docker Desktop or install the `docker-compose-plugin`
package.

---

## 2. Get the code

```bash
# If you have the repo as a folder already, just cd into it.
cd AI-Finance-coach/app
```

All Docker commands below are run from the **`app/`** directory (the one
containing `docker-compose.yml`).

---

## 3. (Optional) Configure API keys

Skip this entirely for a no-key demo run. To enable AI features:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```dotenv
OPENROUTER_API_KEY=sk-or-...            # enables LLM features
JWT_SECRET=some-long-random-string      # recommended for anything non-local
```

Compose reads this `.env` automatically — no need to export variables. (You can
also pass a key inline for a one-off: `OPENROUTER_API_KEY=sk-or-... docker
compose up --build`.)

---

## 4. Build and run

```bash
docker compose up --build
```

What happens:
- The backend and frontend images are built (first build pulls base images and
  installs dependencies — a few minutes; later builds are cached and fast).
- Postgres and Qdrant images are pulled and started.
- Compose waits for Postgres to be healthy before starting the backend.

**First run note:** if you keep the default Qdrant setup, the backend downloads a
small embedding model (~90 MB) the first time it indexes a document. This needs
internet access once; it is cached in the image layer/container afterwards.

When the logs settle, open:

- **App:** <http://localhost:5173>
- **API docs (Swagger):** <http://localhost:8000/docs>
- **Health/capabilities:** <http://localhost:8000/health>

In the UI, click **“Load sample data”** to populate transactions and explore.

### Run in the background
```bash
docker compose up --build -d        # detached
docker compose logs -f              # follow logs
docker compose logs -f backend      # just the backend
```

### Stop / restart / clean up
```bash
docker compose stop                 # stop containers, keep data
docker compose down                 # stop + remove containers (keeps named volumes)
docker compose down -v              # also delete Postgres + Qdrant data (full reset)
docker compose up --build           # rebuild after code changes
```

---

## 5. Verify it works

```bash
# Backend health (lists which capabilities are active)
curl http://localhost:8000/health

# Container status — all should be "running"/"healthy"
docker compose ps
```

The header badge in the UI flips to **“AI narration”** when an
`OPENROUTER_API_KEY` is set; otherwise it shows deterministic mode. The
`/health` response reports every active capability (LLM, Postgres, Qdrant,
OAuth).

---

## 6. Customising

### Change the host ports
Edit the `ports` mappings in `docker-compose.yml` (left side = host):

```yaml
  frontend:
    ports:
      - "8080:80"     # serve the app on http://localhost:8080 instead
```

If you change the frontend port, also update `FRONTEND_URL` and `CORS_ORIGINS`
in `.env` to match (e.g. `http://localhost:8080`).

### Run without Postgres/Qdrant (lightweight)
The backend works standalone with SQLite + TF-IDF. To run just the API +
frontend, you can comment out the `db`/`qdrant` services and set, in `.env`:

```dotenv
DATABASE_URL=sqlite:////app/data/financial_coach.db
QDRANT_URL=
```

(Then remove the `db`/`qdrant` entries from the backend's `depends_on`.)

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `docker: command not found` | Docker isn’t installed / not on PATH — see step 1. |
| `Cannot connect to the Docker daemon` | Start Docker Desktop (or `sudo systemctl start docker` on Linux). |
| `port is already allocated` (5173/8000) | Another process uses the port. Stop it, or remap the host port in `docker-compose.yml`. |
| Frontend loads but API calls fail | Check `docker compose logs backend`; ensure the backend is healthy (`docker compose ps`). |
| `docker compose` not recognized | You have the legacy v1 binary. Install the Compose plugin or use `docker-compose` (with a hyphen). |
| First document upload is slow | Embedding model download on first use — one-time, needs internet. |
| Want a totally clean slate | `docker compose down -v` removes all containers **and** data volumes. |

View logs for any single service to diagnose:
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```
