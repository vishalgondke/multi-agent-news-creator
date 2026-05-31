"""APScheduler setup: run the pipeline daily at 00:00 IST (Asia/Kolkata)."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.orchestration.workflow import run_pipeline

log = logging.getLogger("scheduler")

scheduler = AsyncIOScheduler(timezone=settings.schedule_tz)


async def _job():
    log.info("Scheduled daily pipeline starting")
    await run_pipeline(with_video=True)


def start_scheduler() -> AsyncIOScheduler:
    trigger = CronTrigger(
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        timezone=settings.schedule_tz,
    )
    scheduler.add_job(_job, trigger, id="daily_pipeline", replace_existing=True)
    scheduler.start()
    log.info(
        "Scheduler started: daily at %02d:%02d %s",
        settings.schedule_hour,
        settings.schedule_minute,
        settings.schedule_tz,
    )
    return scheduler
