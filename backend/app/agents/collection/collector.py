"""Collection agent: fetch feeds per domain, dedup, persist raw_items."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.collection.sources import Source, sources_for
from app.core.config import settings
from app.core.constants import DOMAINS
from app.models.db_models import RawItem
from app.services.dedup import content_hash

log = logging.getLogger("collector")

MAX_ITEMS_PER_SOURCE = 15
HTTP_TIMEOUT = 20.0


def _mock_entries(src: Source) -> list[dict]:
    return [
        {
            "title": f"[{src.domain}] Sample headline {i} from {src.name}",
            "link": f"https://example.com/{src.domain}/{i}",
            "summary": f"Mock body text for {src.domain} item {i}. "
            "Used when MOCK_MODE is on so the pipeline runs without network.",
            "published_parsed": None,
        }
        for i in range(1, 4)
    ]


async def _fetch_feed(client: httpx.AsyncClient, src: Source) -> list[dict]:
    if settings.mock_collect:
        return _mock_entries(src)
    try:
        resp = await client.get(src.url, follow_redirects=True, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        return parsed.entries[:MAX_ITEMS_PER_SOURCE]
    except Exception as exc:  # noqa: BLE001 - one bad feed shouldn't kill the run
        log.warning("Failed to fetch %s: %s", src.name, exc)
        return []


def _published(entry: dict) -> datetime | None:
    tm = entry.get("published_parsed") or entry.get("updated_parsed")
    if tm:
        return datetime.fromtimestamp(mktime(tm), tz=timezone.utc).replace(tzinfo=None)
    return None


async def collect_domain(session: AsyncSession, domain: str) -> int:
    """Fetch all sources for a domain; insert new (deduped) raw items. Returns count."""
    srcs = sources_for(domain)
    inserted = 0
    async with httpx.AsyncClient(headers={"User-Agent": "MarketNewsBot/0.1"}) as client:
        feeds = await asyncio.gather(*[_fetch_feed(client, s) for s in srcs])

    for src, entries in zip(srcs, feeds):
        for e in entries:
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            if not title or not link:
                continue
            h = content_hash(title, link)

            exists = await session.scalar(
                select(RawItem.id).where(RawItem.content_hash == h)
            )
            if exists:
                continue

            body = (e.get("summary") or e.get("description") or "")[:8000]
            session.add(
                RawItem(
                    domain=domain,
                    source_url=link,
                    source_name=src.name,
                    content_hash=h,
                    title=title[:2000],
                    body=body,
                    published_at=_published(e),
                    reliability=src.reliability,
                )
            )
            inserted += 1

    await session.commit()
    log.info("Collected %d new items for %s", inserted, domain)
    return inserted


async def collect_all(session: AsyncSession) -> dict[str, int]:
    counts = {}
    for domain in DOMAINS:
        counts[domain] = await collect_domain(session, domain)
    return counts
