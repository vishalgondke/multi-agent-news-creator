# 📈 Market & Tech News Content Creator

A **multi-agent system** that automatically researches, analyzes, and generates daily
content across four domains — **Stocks & Mutual Funds, Commodities, Artificial
Intelligence, and Semiconductors** — and publishes it to a React web app plus an
auto-generated ~1-minute summary video.

Content refreshes **daily at 12:00 AM IST**.

> Pipeline at a glance: **live RSS feeds → dedupe → LLM summaries / impact / trends →
> per-domain web digests → narrated summary video (MP4)**.

---

## ✨ Features

- **Four domain tabs** — Stocks & Mutual Funds, Commodities, AI, Semiconductors.
- **Each tab shows** latest developments, AI-written summaries, key bullet insights,
  market-impact chips (sentiment + tickers), trend banners, and links back to the
  original sources.
- **Multi-agent pipeline** — separate collection, analysis, and synthesis agents.
- **Pluggable LLM provider** — OpenAI, Google Gemini, or Groq, with automatic fallback.
- **Daily summary video** — script written by the LLM, rendered to a real 720p MP4
  (captions per domain; optional voiceover if a TTS key is set).
- **Graceful degradation** — every external dependency has a fallback, so the pipeline
  always completes:
  - No LLM key / rate-limited → headline-based summaries & video script.
  - No TTS key → silent captioned video.
  - `MOCK_MODE=1` → fully deterministic run with zero network/API calls.
- **Zero-setup database** — runs on **SQLite** out of the box; **MySQL** (via Docker)
  is supported by flipping one env var.

---

## 🖼️ Screenshots

> Run the app locally (see [Quick start](#-quick-start)) and drop screenshots in
> `docs/screenshots/`, then they'll render below.

| Domain tab (cards + trends) | Daily summary video |
|---|---|
| ![Domain tab](docs/screenshots/domain-tab.png) | ![Video panel](docs/screenshots/video-panel.png) |

To capture them: open <http://localhost:5173>, click through the tabs, then click
**Daily Video**.

---

## 🏗️ Architecture

```
                 ┌──────────────────────────────────────────┐
                 │  Orchestration  (APScheduler @ 00:00 IST)  │
                 └───────────────────────┬────────────────────┘
                                         │ run_pipeline()
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────┐              ┌──────────────────┐              ┌──────────────────┐
│  COLLECTION   │              │     ANALYSIS     │              │    SYNTHESIS     │
│   (per domain)│              │                  │              │                  │
│  RSS fetch    │  raw_items   │ summarizer       │  summaries   │ web_content      │
│  + dedupe     │ ───────────► │ impact           │ ───────────► │  (digests)       │
│               │              │ trend            │  trends      │ script + video   │
└───────────────┘              └──────────────────┘              └────────┬─────────┘
        │                                                                  │
        ▼                                                                  ▼
┌─────────────────────────── Database (SQLite / MySQL) ───────────────────────────┐
│  raw_items · summaries · clusters · trends · impact_assessments · digests ·      │
│  videos · pipeline_runs                                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
        │                                                                  │
        ▼                                                                  ▼
   FastAPI REST  ◄──────────────  React + Vite frontend  ──────────►  /media/*.mp4
```

### Agents

| Stage | Agent | Responsibility |
|---|---|---|
| Collection | `collector` | Fetch RSS feeds per domain, dedupe via SHA-256 of normalized title+host, persist `raw_items`. |
| Analysis | `summarizer` | LLM → headline, 3–4 bullets, ~200-word deep summary per item. |
| Analysis | `impact` | LLM → tickers, sentiment, price-impact, affected companies, confidence. |
| Analysis | `trend` | LLM → 2–4 trends per domain over a 7-day window with momentum. |
| Synthesis | `web_content` | Assemble the per-domain digest JSON the frontend reads. |
| Synthesis | `script` | Write a ~60s narration script spanning all four domains. |
| Synthesis | `video` | Pillow-drawn frames → MoviePy `ImageClip` → H.264 MP4 (+ optional TTS). |

---

## 🧰 Tech Stack

| Layer | Tech |
|---|---|
| Orchestration | APScheduler (cron @ 00:00 `Asia/Kolkata`) |
| LLM | OpenAI / Google Gemini / Groq (OpenAI-compatible), pluggable via `LLM_PROVIDER` |
| Backend API | FastAPI (async) + SQLAlchemy 2.0 (async) |
| Database | SQLite (default) or MySQL 8 (Docker) |
| Frontend | React 18 + TypeScript + Vite + TanStack Query |
| Video | MoviePy 2.x + Pillow + bundled ffmpeg (`imageio-ffmpeg`) — no system ffmpeg/ImageMagick needed |

---

## 🚀 Quick start

### Prerequisites
- **Python 3.10+** and **`uv`** (or `pip`)
- **Node.js 18+**
- *(optional)* **Docker** — only if you want MySQL instead of SQLite

### 1. Backend

```powershell
cd backend
uv venv
.venv\Scripts\activate
uv pip install -e .

copy .env.example .env   # then edit .env (see Configuration below)
```

Run the full pipeline once (instead of waiting for midnight):

```powershell
python -m app.orchestration.run_once            # with video
python -m app.orchestration.run_once --no-video # skip the video step
```

Start the API:

```powershell
uvicorn app.api.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs> · health check: <http://localhost:8000/health>

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

App: <http://localhost:5173> (Vite proxies `/v1` and `/media` to the backend on `:8000`).

### Enable real MP4 rendering (optional)

The video extra is ~60 MB (numpy, imageio, Pillow):

```powershell
cd backend
uv pip install -e ".[video]"
```

Without it, the video step still runs and saves the narration **script**; with it,
a real captioned 1280×720 MP4 is produced under `backend/media/`.

---

## ⚙️ Configuration

All settings live in `backend/.env` (see `.env.example`). Key options:

```ini
# LLM provider: "openai" | "gemini" | "groq" | "auto"
# auto picks whichever key is set (priority: openai > gemini > groq)
LLM_PROVIDER=auto
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# Database: "sqlite" (zero-setup) or "mysql" (Docker)
DB_BACKEND=sqlite
SQLITE_PATH=./marketnews.db

# Schedule (IST midnight by default)
SCHEDULE_TZ=Asia/Kolkata
SCHEDULE_HOUR=0
SCHEDULE_MINUTE=0

# Set to 1 for a deterministic offline run (no network / no API calls)
MOCK_MODE=0
```

> **Security:** `.env` is git-ignored. Never commit real API keys. If a key is ever
> exposed, rotate it.

### Using MySQL instead of SQLite

```powershell
docker compose -f infra/docker-compose.yml up -d   # MySQL 8 on host port 3308 + Redis
```

Then set `DB_BACKEND=mysql` and `DB_PORT=3308` in `.env`. The schema is auto-applied
from `backend/app/db/init.sql`. (Host port **3308** is used to avoid clashing with a
local MySQL already on 3306.)

---

## 🔌 API

Base URL: `http://localhost:8000/v1`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/digests/all` | Latest digest for all four domains |
| `GET` | `/digests/{domain}` | Latest digest for one domain |
| `GET` | `/digests/{domain}/history` | Past digests (paginated) |
| `GET` | `/trends/{domain}` | Trends for a domain (`?period_days=7`) |
| `GET` | `/items/{domain}` | Raw collected items (`?limit&offset`) |
| `GET` | `/videos/latest` | Latest completed video metadata + `media_url` |
| `GET` | `/videos` | List recent videos |
| `POST` | `/videos/generate` | Trigger video generation (runs in background) |
| `GET` | `/videos/{id}` | Single video status |
| `GET` | `/health` | Status, resolved LLM provider, DB backend |

`domain` ∈ `stocks` · `commodities` · `ai` · `semiconductors`

---

## 🗄️ Database schema

`raw_items` · `summaries` · `clusters` · `trends` · `impact_assessments` ·
`digests` · `videos` · `pipeline_runs`

The ORM models (`backend/app/models/db_models.py`) work unchanged on both SQLite and
MySQL. The canonical MySQL DDL is in `backend/app/db/init.sql`; SQLite tables are
auto-created on startup via `init_db()`.

---

## 📁 Project structure

```
market-news-content-creator/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── collection/        # sources.py, collector.py
│   │   │   ├── analysis/          # summarizer.py, impact.py, trend.py
│   │   │   └── synthesis/         # web_content.py, script.py, video.py
│   │   ├── api/
│   │   │   ├── main.py            # FastAPI app + lifespan + /media mount
│   │   │   └── routers/           # digests, trends, items, videos
│   │   ├── core/                  # config.py, database.py, constants.py
│   │   ├── models/db_models.py    # SQLAlchemy ORM
│   │   ├── schemas/               # Pydantic response models
│   │   ├── services/              # llm.py (provider dispatch), dedup.py, tts.py
│   │   ├── orchestration/         # workflow.py, scheduler.py, run_once.py
│   │   └── db/init.sql            # MySQL schema
│   ├── media/                     # generated videos + scripts (git-ignored)
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/            # TabNav, DomainTab, DigestCard, TrendBanner, VideoPanel
│   │   ├── hooks/                 # useDigest, useLatestVideo
│   │   ├── api/client.ts
│   │   ├── types.ts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── infra/
│   └── docker-compose.yml         # MySQL 8 + Redis
└── README.md
```

---

## 🔁 Scheduling

`app/orchestration/scheduler.py` registers an APScheduler cron job that runs
`run_pipeline()` daily at the configured time (default **00:00 Asia/Kolkata**). The
scheduler starts automatically with the FastAPI app. Each run is recorded in the
`pipeline_runs` table with stats and status.

---

## 🧪 Data sources

RSS/Atom feeds with per-source reliability weights, e.g.:

- **Stocks** — Reuters, CNBC Markets, MarketWatch, Investing.com
- **Commodities** — CNBC Commodities, Investing.com, OilPrice.com
- **AI** — Google AI Blog, MIT Tech Review, VentureBeat AI, ArXiv `cs.AI`
- **Semiconductors** — AnandTech, Tom's Hardware, EE Times, SemiEngineering

Add or swap sources in `backend/app/agents/collection/sources.py`.

---

## 📝 Notes & limitations

- **Free LLM tiers rate-limit.** Groq's free tier caps daily tokens and ~30 req/min;
  the client retries with backoff and falls back to headline-based output if exhausted.
- **Video has no voiceover unless a TTS key is configured** (OpenAI TTS / ElevenLabs).
  Without it you get a silent captioned MP4.
- **Embeddings/clustering** are scaffolded (`clusters` table) but the similarity step
  is left as a future enhancement; summaries currently map 1:1 to raw items.

---

## 📜 License

MIT — see `LICENSE` (add one before publishing if desired).
