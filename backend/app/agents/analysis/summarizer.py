"""Summarizer agent: turns raw items into structured summaries via Claude."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAIN_LABELS, DOMAINS
from app.models.db_models import RawItem, Summary
from app.services.llm import complete_json

log = logging.getLogger("summarizer")

SYSTEM = """You are a financial & technology news editor.
Summarize the given news item for a {label} briefing.
Return STRICT JSON with this exact shape:
{{
  "headline": "<=12 word punchy headline",
  "bullets": ["3 to 4 short bullets, each <=15 words"],
  "deep_summary": "<=200 word analytical paragraph: what happened, why it matters, who is affected"
}}
Only output JSON. No markdown, no commentary."""

LOOKBACK_HOURS = 36
MAX_PER_DOMAIN = 12


def _mock_summary(item: RawItem):
    return {
        "headline": item.title[:80],
        "bullets": [
            "Key point one about the development.",
            "Key point two with market context.",
            "Key point three on likely impact.",
        ],
        "deep_summary": (item.body or item.title)[:200] or "Mock analytical summary.",
    }


async def _unsummarized(session: AsyncSession, domain: str) -> list[RawItem]:
    cutoff = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
    stmt = (
        select(RawItem)
        .outerjoin(Summary, Summary.raw_item_id == RawItem.id)
        .where(RawItem.domain == domain)
        .where(RawItem.collected_at >= cutoff)
        .where(Summary.id.is_(None))
        .order_by(RawItem.reliability.desc(), RawItem.collected_at.desc())
        .limit(MAX_PER_DOMAIN)
    )
    return list((await session.scalars(stmt)).all())


async def summarize_domain(session: AsyncSession, domain: str) -> int:
    items = await _unsummarized(session, domain)
    system = SYSTEM.format(label=DOMAIN_LABELS[domain])
    created = 0
    for item in items:
        user = f"TITLE: {item.title}\n\nCONTENT:\n{item.body or '(no body)'}"
        try:
            data = complete_json(
                system=system,
                user=user,
                max_tokens=600,
                mock_fn=lambda it=item: _mock_summary(it),
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Summarize failed for %s: %s", item.id, exc)
            continue

        session.add(
            Summary(
                raw_item_id=item.id,
                domain=domain,
                headline=str(data.get("headline", item.title))[:500],
                bullets=data.get("bullets", [])[:5],
                deep_summary=str(data.get("deep_summary", ""))[:4000],
            )
        )
        created += 1

    await session.commit()
    log.info("Summarized %d items for %s", created, domain)
    return created


async def summarize_all(session: AsyncSession) -> dict[str, int]:
    return {d: await summarize_domain(session, d) for d in DOMAINS}
