"""Raw item endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAINS
from app.core.database import get_session
from app.models.db_models import RawItem

router = APIRouter(prefix="/v1/items", tags=["items"])


@router.get("/{domain}")
async def list_items(
    domain: str,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    if domain not in DOMAINS:
        raise HTTPException(404, f"Unknown domain '{domain}'")
    rows = (
        await session.scalars(
            select(RawItem)
            .where(RawItem.domain == domain)
            .order_by(RawItem.collected_at.desc())
            .limit(min(limit, 100))
            .offset(offset)
        )
    ).all()
    return [
        {
            "id": r.id,
            "domain": r.domain,
            "title": r.title,
            "source_name": r.source_name,
            "source_url": r.source_url,
            "published_at": r.published_at.isoformat() if r.published_at else None,
            "collected_at": r.collected_at.isoformat(),
        }
        for r in rows
    ]
