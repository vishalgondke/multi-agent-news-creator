"""Web content agent: assemble the per-domain digest JSON the frontend reads."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAIN_LABELS, DOMAINS
from app.models.db_models import (
    Digest,
    ImpactAssessment,
    RawItem,
    Summary,
    Trend,
)

log = logging.getLogger("web_content")

LOOKBACK_HOURS = 36
MAX_CARDS = 10


async def build_domain_digest(session: AsyncSession, domain: str) -> str | None:
    cutoff = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
    rows = (
        await session.execute(
            select(Summary, RawItem, ImpactAssessment)
            .join(RawItem, RawItem.id == Summary.raw_item_id)
            .outerjoin(ImpactAssessment, ImpactAssessment.summary_id == Summary.id)
            .where(Summary.domain == domain)
            .where(Summary.created_at >= cutoff)
            .order_by(RawItem.reliability.desc(), Summary.created_at.desc())
            .limit(MAX_CARDS)
        )
    ).all()

    if not rows:
        log.info("No summaries to publish for %s", domain)
        return None

    cards = []
    for summary, raw, impact in rows:
        cards.append(
            {
                "summary_id": summary.id,
                "headline": summary.headline,
                "bullets": summary.bullets,
                "deep_summary": summary.deep_summary,
                "source_name": raw.source_name,
                "source_url": raw.source_url,
                "published_at": raw.published_at.isoformat() if raw.published_at else None,
                "impact": (
                    {
                        "tickers": impact.tickers or [],
                        "sentiment": impact.sentiment,
                        "price_impact": impact.price_impact,
                        "affected_cos": impact.affected_cos or [],
                        "confidence": float(impact.confidence),
                    }
                    if impact
                    else None
                ),
            }
        )

    trends = list(
        (
            await session.scalars(
                select(Trend)
                .where(Trend.domain == domain)
                .order_by(Trend.created_at.desc())
                .limit(4)
            )
        ).all()
    )
    trend_payload = [
        {
            "id": t.id,
            "domain": t.domain,
            "title": t.title,
            "description": t.description,
            "momentum": t.momentum,
            "created_at": t.created_at.isoformat(),
        }
        for t in trends
    ]

    content = {
        "domain": domain,
        "domain_label": DOMAIN_LABELS[domain],
        "cards": cards,
        "trends": trend_payload,
    }

    digest = Digest(domain=domain, content=content)
    session.add(digest)
    await session.commit()
    log.info("Published digest for %s (%d cards)", domain, len(cards))
    return digest.id


async def build_all(session: AsyncSession) -> dict[str, str | None]:
    return {d: await build_domain_digest(session, d) for d in DOMAINS}
