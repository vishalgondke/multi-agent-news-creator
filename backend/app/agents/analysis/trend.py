"""Trend agent: analyze a rolling window of summaries to surface trends."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOMAIN_LABELS, DOMAINS
from app.models.db_models import Summary, Trend
from app.services.llm import complete_json

log = logging.getLogger("trend")

SYSTEM = """You are a {label} trend analyst. Given recent headlines, identify the
2-4 most important trends. Return STRICT JSON:
{{
  "trends": [
    {{
      "title": "short trend name",
      "description": "<=60 word explanation of the trend and why it matters",
      "momentum": "new | accelerating | plateauing | declining"
    }}
  ]
}}
Only output JSON."""

WINDOW_DAYS = 7
VALID_MOMENTUM = {"new", "accelerating", "plateauing", "declining"}


def _mock_trends(domain: str):
    return {
        "trends": [
            {
                "title": f"{DOMAIN_LABELS[domain]} momentum",
                "description": "Mock trend generated in MOCK_MODE for pipeline testing.",
                "momentum": "new",
            }
        ]
    }


async def trend_domain(session: AsyncSession, domain: str) -> int:
    start = datetime.utcnow() - timedelta(days=WINDOW_DAYS)
    end = datetime.utcnow()
    headlines = list(
        (
            await session.scalars(
                select(Summary.headline)
                .where(Summary.domain == domain)
                .where(Summary.created_at >= start)
                .order_by(Summary.created_at.desc())
                .limit(50)
            )
        ).all()
    )
    if not headlines:
        return 0

    user = "RECENT HEADLINES:\n" + "\n".join(f"- {h}" for h in headlines)
    try:
        data = complete_json(
            system=SYSTEM.format(label=DOMAIN_LABELS[domain]),
            user=user,
            max_tokens=700,
            mock_fn=lambda: _mock_trends(domain),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Trend failed for %s: %s", domain, exc)
        return 0

    # replace today's trends for this domain
    await session.execute(
        delete(Trend).where(Trend.domain == domain).where(Trend.period_end >= start)
    )

    created = 0
    for t in data.get("trends", [])[:4]:
        momentum = t.get("momentum", "new")
        session.add(
            Trend(
                domain=domain,
                title=str(t.get("title", ""))[:500],
                description=str(t.get("description", ""))[:2000],
                momentum=momentum if momentum in VALID_MOMENTUM else "new",
                period_start=start,
                period_end=end,
            )
        )
        created += 1

    await session.commit()
    log.info("Created %d trends for %s", created, domain)
    return created


async def trend_all(session: AsyncSession) -> dict[str, int]:
    return {d: await trend_domain(session, d) for d in DOMAINS}
