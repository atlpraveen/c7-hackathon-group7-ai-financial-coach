# 💰 AI Financial Coach Agent

A **personalised, multi-agent financial advisor for India (₹ INR)**. Upload your
real financial documents (transactions CSV, statements) and a team of specialist
AI agents — **debt analyser**, **savings strategist**, **budget advisor**,
**investment educator**, **portfolio optimizer**, and an **Indian tax &
retirement planner** — analyse your money and produce a single, prioritised
action plan on a live dashboard.

It is built so it **runs end-to-end with zero setup** (deterministic reasoning,
SQLite, in-process search) and **upgrades automatically** when you add an
OpenRouter key, Postgres, or Qdrant.

| Capability | Where it lives |
|---|---|
| 🧠 **LLM routing** (OpenRouter) | `agents/orchestrator.py` → `llm/openrouter.py` picks the relevant agents semantically (keyword fallback) |
| 🕸️ **LangGraph orchestration** | `agents/graph.py` — router → parallel agent nodes → synthesis StateGraph (asyncio fallback) |
| 🔎 **Qdrant vector search** | `rag/vector_store.py` — fastembed embeddings + Qdrant, per-user collections (TF-IDF fallback) |
| 🔐 **JWT / Google OAuth auth** | `auth/` — stdlib PBKDF2 + HS256 JWT, optional Google OAuth |
| 📡 **Real-time streaming** | `coach/ask/stream` Server-Sent Events, token-by-token |
| 🐘 **PostgreSQL analytics** | `db/` (SQLAlchemy) + `db/repository.py` SQL aggregations (spend trends, MoM, category mix) |
| 👥 **Multi-user architecture** | per-user data, vector collections, and sessions (`api/state.py`) |
| 💬 **Conversation memory** | `conversations`/`messages` tables threaded into every LLM call |
| 🏷️ **AI transaction categorization** | `services/categorization.py` — LLM + Indian-merchant keyword tiers |
| 📈 **Portfolio optimization** | `tools/portfolio_tools.py` — Markowitz mean-variance / efficient frontier (numpy) |
| 🎯 **Financial goal tracking** | `services/goals.py` + `goals` table — progress, projections, required contributions |
| 🇮🇳 **Indian finance** | `tools/india_tools.py` — EPF, NPS, ELSS, SIP, old-vs-new **tax regime** |
| 🤖 **Agent orchestration · tabular RAG · dashboard** | `agents/`, `rag/`, `frontend/` |

---

## ✨ Feature highlights

- **Debt analyser** — avalanche vs snowball month-by-month, months-to-debt-free,
  total interest, payoff order.
- **Savings strategist** — emergency-fund target/gap, savings rate vs benchmark,
  per-goal funding schedules.
- **Budget advisor** — 50/30/20 classification, overspend flags, top categories.
- **Investment educator** — risk/age allocation with compound-growth projection.
- **Portfolio optimizer** — mean-variance optimisation over an Indian asset
  universe (equity / debt / gold / international), efficient frontier, Sharpe,
  and a ₹ monthly allocation.
- **India · Tax & Retirement** — EPF & NPS corpus projections, ELSS 80C tax
  saving, SIP wealth, and an **old-vs-new tax regime** comparison (FY 2024-25).
- **Goal tracking** — create goals, watch progress, see the monthly contribution
  required to hit each deadline.
- **Analytics** — month-over-month spend, category mix, income/expense trends.
- **Ask the Coach** — streaming chat grounded in your documents + memory.
- **Runs with zero keys.** Every number is deterministic; keys/services only
  upgrade narration, routing, search, and persistence.

---

## 🏗️ Architecture

```
                       ┌────────────────────────────────────────────────┐
                       │                 FRONTEND (React)                │
                       │  Vite · TS · Tailwind · Recharts · Zustand      │
                       │  Dashboard · Transactions · Analytics · Debt    │
                       │  Savings · Budget · Investments · Portfolio     │
                       │  India · Goals · Ask-the-Coach (streaming)      │
                       └───────────────────────┬────────────────────────┘
                                               │  REST + SSE  ( JWT bearer )
                                               ▼
   ┌──────────────────────────────────────────────────────────────────────────┐
   │                            BACKEND (FastAPI)                               │
   │  /auth (JWT/OAuth)  /documents  /transactions  /analytics  /goals          │
   │  /debt /savings /budget /investment /portfolio /india                      │
   │  /coach/review (orchestrated)   /coach/ask + /coach/ask/stream (RAG)        │
   │                                                                            │
   │  ┌─────────────── ORCHESTRATOR ───────────────┐   ┌──────────────────────┐ │
   │  │ LLM router (OpenRouter) → LangGraph graph   │   │  LLM LAYER (optional) │ │
   │  │ router → [agents in parallel] → synthesis   │   │  OpenRouter chat /    │ │
   │  └───┬───────┬───────┬───────┬───────┬─────┬───┘   │  stream / route /     │ │
   │      ▼       ▼       ▼       ▼       ▼     ▼       │  categorize           │ │
   │   Debt  Savings  Budget Invest Portfolio India     └──────────────────────┘ │
   │      └───────┴───────┴───────┴───────┴─────┘  →  deterministic TOOLS engine  │
   │                                                                            │
   │  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐ │
   │  │ TABULAR RAG           │  │ PERSISTENCE (SQLAlch)│  │ AUTH              │ │
   │  │ parse → categorize    │  │ users · transactions │  │ PBKDF2 + HS256 JWT│ │
   │  │ → profile extractor   │  │ goals · conversations│  │ Google OAuth      │ │
   │  │ → Qdrant / TF-IDF      │  │ Postgres / SQLite    │  │                   │ │
   │  └──────────────────────┘  └──────────────────────┘  └───────────────────┘ │
   └──────────────────────────────────────────────────────────────────────────┘
```

**Two-stage agents:** every agent first runs deterministic tools over your
profile (the *facts*), then narrates them — via OpenRouter when a key is set,
otherwise a built-in templated narrator. **The numbers are identical either way.**

### Graceful degradation — set a key/URL to light up each backend

| Env var | Off (default) | On |
|---|---|---|
| `OPENROUTER_API_KEY` | deterministic narration, **keyword** routing | LLM narration, **semantic** routing, AI categorization, streaming |
| `DATABASE_URL` | local **SQLite** file | **PostgreSQL** (set `postgresql://…`) |
| `QDRANT_URL` | embedded Qdrant `:memory:` → falls back to **TF-IDF** if fastembed/Qdrant unavailable | **Qdrant** vector search (`:memory:`, a path, or an `http://` server) |
| `GOOGLE_CLIENT_ID/SECRET` | JWT email/password only | **Google OAuth** login |

### Project layout

```
app/
├── backend/
│   ├── src/
│   │   ├── tools/      # debt, savings, budget, investment, portfolio (MPT), india (EPF/NPS/ELSS/SIP/tax)
│   │   ├── rag/        # csv/pdf parse, profile extractor, vector_store (Qdrant/TF-IDF), rag_service
│   │   ├── agents/     # base + 6 specialists + orchestrator + LangGraph graph
│   │   ├── llm/        # openrouter client + unified narration facade
│   │   ├── auth/       # PBKDF2 + JWT + Google OAuth
│   │   ├── db/         # SQLAlchemy engine, models, repository (+ analytics SQL)
│   │   ├── services/   # AI categorization, goal tracking
│   │   ├── core/       # config + logging
│   │   └── api/        # FastAPI app, schemas, per-user state, routes
│   ├── sample_data/transactions.csv   # 3 months of realistic Indian (₹) transactions
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/      # Dashboard, Data, Transactions, Analytics, Debt, Savings, Budget,
        │               # Investment, PortfolioOptimizer, IndiaFinance, Goals, Coach
        ├── components/ # Sidebar, Header, charts, ui primitives, AuthModal
        ├── api/client.ts  # typed fetch + JWT + SSE streaming
        └── store.ts    # zustand state + actions
```

---

## 🚀 Getting started

**Prerequisites:** Python 3.9+ and Node.js 18+. (No external services required —
SQLite + TF-IDF are built in.)

### Option A — two terminals (dev)

```bash
# 1) Backend
cd app/backend
./run.sh                       # venv + deps + serves http://localhost:8000  (docs at /docs)

# 2) Frontend
cd app/frontend
npm install && npm run dev     # http://localhost:5173
```

Open **http://localhost:5173** and click **“Load sample data”**.

> Heads-up on Python 3.9: `numpy` is pinned as `>=1.26` so it resolves on 3.9
> (newer Pythons get a later 2.x). The Docker image uses Python 3.11.

### Option B — Docker (recommended; runs anywhere)

The only prerequisite is **Docker Desktop / Docker Engine** (with the Compose
plugin). No Python, Node, Postgres or Qdrant needed on the host — everything is
built into images.

```bash
cd app
docker compose up --build
# Postgres + Qdrant + backend + frontend all start automatically.
# Open the app at http://localhost:5173   (API docs at http://localhost:8000/docs)
```

To enable the AI features, create `app/.env` (`cp .env.example .env`) and set
`OPENROUTER_API_KEY`, then `docker compose up --build` again.

📖 **Full step-by-step Docker guide (install, run, configure, troubleshoot):
[app/DOCKER.md](app/DOCKER.md).**

### (Optional) Turn on the AI features

```bash
cd app/backend
cp .env.example .env
#   OPENROUTER_API_KEY=sk-or-...        # LLM routing, narration, categorization, streaming
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/financial_coach
#   QDRANT_URL=http://localhost:6333    # or keep :memory:
#   GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
```

The header badge flips to **“AI narration”** and `/health` reports every active
capability.

---

## 🧭 Using the app

1. **Sign in** (top-right) to register / log in / use Google — or stay anonymous
   in the shared **guest** workspace. Logged-in users get isolated data.
2. **Data & Profile** → **Load sample data** (or upload your own CSV/PDF). The
   coach parses it, **AI-categorizes** transactions, indexes them for Q&A, and
   stores them for analytics.
3. **Transactions** → see every row, re-run **AI categorization**.
4. **Analytics** → month-over-month spend, category mix, income/expense trends.
5. **Debt / Savings / Budget / Investments / Portfolio / India** → each
   specialist agent's analysis with interactive ₹ charts.
6. **Goals** → create and track goals with progress + required-contribution math.
7. **Ask the Coach** → streaming chat grounded in your documents and memory, or a
   one-click **full orchestrated review** (LLM-routed via LangGraph).

---

## 🔌 API reference (selected)

| Method | Endpoint | Purpose |
|---|---|---|
| `GET`  | `/health` | status + every active capability |
| `POST` | `/auth/register` · `/auth/login` | JWT auth |
| `GET`  | `/auth/google/login` · `/auth/google/callback` | Google OAuth |
| `POST` | `/documents/upload` · `/documents/sample` | ingest CSV/PDF/TXT |
| `GET`  | `/transactions` · `POST /transactions/categorize` | list + AI-categorize |
| `GET`  | `/analytics/summary` | Postgres-backed analytics |
| `GET/POST/PUT/DELETE` | `/goals` | goal tracking CRUD + progress |
| `POST` | `/debt/analyze` `/savings/plan` `/budget/analyze` `/investment/recommend` | specialists |
| `POST` | `/portfolio/optimize` `/india/plan` | optimizer + Indian finance |
| `POST` | `/coach/review` | **LLM-routed, LangGraph-orchestrated** review |
| `POST` | `/coach/ask` · `/coach/ask/stream` | RAG Q&A (+ SSE streaming) with memory |

Interactive docs: **http://localhost:8000/docs**.

---

## 🛠️ Tech stack

**Backend:** FastAPI · Pydantic · SQLAlchemy (SQLite/Postgres) · LangGraph ·
Qdrant + fastembed · OpenRouter (OpenAI-compatible) · numpy · pandas · pypdf ·
stdlib JWT/PBKDF2.
**Frontend:** React 18 · TypeScript · Vite · Tailwind CSS · Recharts · Zustand.

## ⚠️ Disclaimer

Educational software. Financial, investment, and tax outputs (including the
Indian tax-regime comparison) are **illustrative** and **not** personalised
financial or tax advice. Verify against current rules before acting.
