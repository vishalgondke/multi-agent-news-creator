"""Pipeline orchestration: collect -> analyze -> synthesize.

A linear DAG kept dependency-free (no LangGraph needed for this shape). Each
stage is idempotent and records a row in pipeline_runs for auditing.
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.agents.analysis.impact import assess_all
from app.agents.analysis.summarizer import summarize_all
from app.agents.analysis.trend import trend_all
from app.agents.collection.collector import collect_all
from app.agents.synthesis.video import generate_video
from app.agents.synthesis.web_content import build_all
from app.core.database import SessionLocal
from app.models.db_models import PipelineRun

log = logging.getLogger("workflow")


async def run_pipeline(with_video: bool = True) -> dict:
    """Execute the full daily pipeline. Returns a stats dict."""
    from app.core.database import init_db

    await init_db()  # idempotent; ensures tables exist (esp. for SQLite)
    async with SessionLocal() as session:
        run = PipelineRun(status="running")
        session.add(run)
        await session.commit()
        run_id = run.id

    stats: dict = {}
    try:
        async with SessionLocal() as s:
            stats["collected"] = await collect_all(s)
        async with SessionLocal() as s:
            stats["summarized"] = await summarize_all(s)
        async with SessionLocal() as s:
            stats["impact"] = await assess_all(s)
        async with SessionLocal() as s:
            stats["trends"] = await trend_all(s)
        async with SessionLocal() as s:
            stats["digests"] = await build_all(s)
        if with_video:
            async with SessionLocal() as s:
                stats["video_id"] = await generate_video(s)

        async with SessionLocal() as s:
            run = await s.get(PipelineRun, run_id)
            run.status = "success"
            run.finished_at = datetime.utcnow()
            run.stats = stats
            await s.commit()
        log.info("Pipeline complete: %s", stats)
    except Exception as exc:  # noqa: BLE001
        log.exception("Pipeline failed")
        async with SessionLocal() as s:
            run = await s.get(PipelineRun, run_id)
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.error = str(exc)[:2000]
            run.stats = stats
            await s.commit()
        raise

    return stats
