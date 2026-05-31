"""Video endpoints."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db_models import Video
from app.agents.synthesis.video import generate_video

router = APIRouter(prefix="/v1/videos", tags=["videos"])


def _serialize(v: Video) -> dict:
    return {
        "id": v.id,
        "status": v.status,
        "file_path": v.file_path,
        "media_url": f"/media/{v.file_path}" if v.file_path else None,
        "duration_s": v.duration_s,
        "script": v.script,
        "created_at": v.created_at.isoformat(),
    }


@router.get("/latest")
async def latest(session: AsyncSession = Depends(get_session)):
    v = await session.scalar(
        select(Video).where(Video.status == "done").order_by(Video.created_at.desc()).limit(1)
    )
    if not v:
        raise HTTPException(404, "No video yet")
    return _serialize(v)


@router.get("")
async def list_videos(limit: int = 20, session: AsyncSession = Depends(get_session)):
    rows = (
        await session.scalars(select(Video).order_by(Video.created_at.desc()).limit(min(limit, 50)))
    ).all()
    return [_serialize(v) for v in rows]


@router.post("/generate")
async def trigger_generate(session: AsyncSession = Depends(get_session)):
    # run in background so the request returns immediately
    asyncio.create_task(_run_generate())
    return {"status": "started"}


async def _run_generate():
    from app.core.database import SessionLocal

    async with SessionLocal() as s:
        await generate_video(s)


@router.get("/{video_id}")
async def get_video(video_id: str, session: AsyncSession = Depends(get_session)):
    v = await session.get(Video, video_id)
    if not v:
        raise HTTPException(404, "Not found")
    return _serialize(v)
