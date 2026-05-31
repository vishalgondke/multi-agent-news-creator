"""Trend endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAINS
from app.core.database import get_session
from app.models.db_models import Trend

router = APIRouter(prefix="/v1/trends", tags=["trends"])


@router.get("/{domain}")
async def get_trends(
    domain: str, period_days: int = 7, session: AsyncSession = Depends(get_session)
):
    if domain not in DOMAINS:
        raise HTTPException(404, f"Unknown domain '{domain}'")
    cutoff = datetime.utcnow() - timedelta(days=period_days)
    rows = (
        await session.scalars(
            select(Trend)
            .where(Trend.domain == domain)
            .where(Trend.created_at >= cutoff)
            .order_by(Trend.created_at.desc())
        )
    ).all()
    return [
        {
            "id": t.id,
            "domain": t.domain,
            "title": t.title,
            "description": t.description,
            "momentum": t.momentum,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]
