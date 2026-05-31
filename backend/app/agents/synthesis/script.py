"""Script agent: write a ~60s (≈150 word) video script spanning all 4 domains."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAIN_LABELS, DOMAINS
from app.models.db_models import RawItem, Summary
from app.services.llm import complete_json

log = logging.getLogger("script")

SYSTEM = """You are a broadcast news script writer. Write a tight ~60 second
voiceover (about 150 words total) summarizing today's top stories across four
domains: Stocks & Mutual Funds, Commodities, AI, and Semiconductors.

Structure & timing:
- intro (~10s)
- one segment per domain (~12s each), lead with the single biggest story
- outro (~6s)

Return STRICT JSON:
{
  "segments": [
    {"domain": "intro|stocks|commodities|ai|semiconductors|outro", "text": "..."}
  ]
}
Keep it natural for narration. Only output JSON."""


def _top_headlines(session, domain):
    cutoff = datetime.utcnow() - timedelta(hours=36)
    return (
        select(Summary.headline)
        .join(RawItem, RawItem.id == Summary.raw_item_id)
        .where(Summary.domain == domain)
        .where(Summary.created_at >= cutoff)
        .order_by(RawItem.reliability.desc(), Summary.created_at.desc())
        .limit(3)
    )


def _fallback_script(heads_by_domain: dict[str, list[str]]) -> dict:
    """Build a script from the real top headlines, no LLM needed.

    Used when the LLM is unavailable (rate limit / no key) so the daily video
    still reflects today's actual stories instead of failing.
    """
    segs = [{"domain": "intro", "text": "Here's your daily market and technology briefing."}]
    for d in DOMAINS:
        heads = heads_by_domain.get(d, [])
        if heads:
            lead = heads[0]
            extra = f" Also: {heads[1]}." if len(heads) > 1 else ""
            text = f"In {DOMAIN_LABELS[d]}: {lead}.{extra}"
        else:
            text = f"In {DOMAIN_LABELS[d]}, no major headlines today."
        segs.append({"domain": d, "text": text})
    segs.append({"domain": "outro", "text": "That's your briefing. Stay ahead of the market."})
    return {"segments": segs}


async def build_script(session: AsyncSession) -> dict:
    heads_by_domain: dict[str, list[str]] = {}
    lines = []
    for d in DOMAINS:
        heads = list((await session.scalars(_top_headlines(session, d))).all())
        heads_by_domain[d] = heads
        lines.append(f"{DOMAIN_LABELS[d]}:\n" + "\n".join(f"- {h}" for h in heads))
    user = "TOP STORIES BY DOMAIN:\n\n" + "\n\n".join(lines)

    try:
        return complete_json(
            system=SYSTEM,
            user=user,
            max_tokens=800,
            mock_fn=lambda: _fallback_script(heads_by_domain),
        )
    except Exception as exc:  # noqa: BLE001 - LLM down/rate-limited: use real headlines
        log.warning("Script LLM call failed (%s); using headline fallback", exc)
        return _fallback_script(heads_by_domain)
