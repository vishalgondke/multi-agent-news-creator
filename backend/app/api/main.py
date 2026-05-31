"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import digests, items, trends, videos
from app.core.config import settings
from app.orchestration.scheduler import scheduler, start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import init_db

    await init_db()
    start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Market & Tech News API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve generated media (videos, scripts)
media_path = Path(settings.media_dir)
media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

app.include_router(digests.router)
app.include_router(trends.router)
app.include_router(videos.router)
app.include_router(items.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_provider": settings.resolved_provider,
        "mock_llm": settings.mock_llm,
        "db_backend": settings.db_backend,
    }
