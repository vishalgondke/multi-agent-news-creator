"""Digest endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAINS
from app.core.database import get_session
from app.models.db_models import Digest

router = APIRouter(prefix="/v1/digests", tags=["digests"])


async def _latest(session: AsyncSession, domain: str) -> dict | None:
    digest = await session.scalar(
        select(Digest)
        .where(Digest.domain == domain)
        .order_by(Digest.generated_at.desc())
        .limit(1)
    )
    if not digest:
        return None
    payload = dict(digest.content)
    payload["id"] = digest.id
    payload["generated_at"] = digest.generated_at.isoformat()
    return payload


@router.get("/all")
async def get_all(session: AsyncSession = Depends(get_session)):
    return {d: await _latest(session, d) for d in DOMAINS}


@router.get("/{domain}")
async def get_domain(domain: str, session: AsyncSession = Depends(get_session)):
    if domain not in DOMAINS:
        raise HTTPException(404, f"Unknown domain '{domain}'")
    payload = await _latest(session, domain)
    if payload is None:
        raise HTTPException(404, "No digest yet. Run the pipeline first.")
    return payload


@router.get("/{domain}/history")
async def get_history(
    domain: str, limit: int = 10, session: AsyncSession = Depends(get_session)
):
    if domain not in DOMAINS:
        raise HTTPException(404, f"Unknown domain '{domain}'")
    rows = (
        await session.scalars(
            select(Digest)
            .where(Digest.domain == domain)
            .order_by(Digest.generated_at.desc())
            .limit(min(limit, 50))
        )
    ).all()
    return [
        {"id": d.id, "generated_at": d.generated_at.isoformat(), "content": d.content}
        for d in rows
    ]
