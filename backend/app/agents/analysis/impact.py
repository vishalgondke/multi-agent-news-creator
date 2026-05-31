"""Impact agent: extract tickers, sentiment, affected companies per summary."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAINS
from app.models.db_models import ImpactAssessment, Summary
from app.services.llm import complete_json

log = logging.getLogger("impact")

SYSTEM = """You are a market impact analyst. Given a news summary, assess its market impact.
Return STRICT JSON:
{
  "tickers": ["relevant stock tickers, [] if none"],
  "sentiment": "positive | negative | neutral",
  "price_impact": "one short sentence on likely price/market effect",
  "affected_cos": ["companies or sectors affected"],
  "confidence": 0.0-1.0
}
Only output JSON."""

LOOKBACK_HOURS = 36


def _mock_impact():
    return {
        "tickers": [],
        "sentiment": "neutral",
        "price_impact": "Limited near-term market impact expected.",
        "affected_cos": [],
        "confidence": 0.4,
    }


async def _unassessed(session: AsyncSession, domain: str) -> list[Summary]:
    cutoff = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
    stmt = (
        select(Summary)
        .outerjoin(ImpactAssessment, ImpactAssessment.summary_id == Summary.id)
        .where(Summary.domain == domain)
        .where(Summary.created_at >= cutoff)
        .where(ImpactAssessment.id.is_(None))
    )
    return list((await session.scalars(stmt)).all())


def _clamp_sentiment(val: str) -> str:
    return val if val in ("positive", "negative", "neutral") else "neutral"


async def assess_domain(session: AsyncSession, domain: str) -> int:
    summaries = await _unassessed(session, domain)
    created = 0
    for s in summaries:
        user = f"HEADLINE: {s.headline}\nSUMMARY: {s.deep_summary}"
        try:
            data = complete_json(
                system=SYSTEM, user=user, max_tokens=400, mock_fn=_mock_impact
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Impact failed for %s: %s", s.id, exc)
            continue

        session.add(
            ImpactAssessment(
                summary_id=s.id,
                tickers=data.get("tickers", [])[:10],
                sentiment=_clamp_sentiment(data.get("sentiment", "neutral")),
                price_impact=str(data.get("price_impact", ""))[:1000] or None,
                affected_cos=data.get("affected_cos", [])[:10],
                confidence=float(data.get("confidence", 0.5)),
            )
        )
        created += 1

    await session.commit()
    log.info("Assessed impact for %d summaries in %s", created, domain)
    return created


async def assess_all(session: AsyncSession) -> dict[str, int]:
    return {d: await assess_domain(session, d) for d in DOMAINS}
