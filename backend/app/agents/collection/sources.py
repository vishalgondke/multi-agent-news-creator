"""Source registry per domain.

Each source is an RSS/Atom feed with a reliability weight (0-1). RSS keeps the
collector dependency-light and works without paid API keys. Swap in REST APIs
(Alpha Vantage, Trading Economics, etc.) by adding entries with kind="api".
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    domain: str
    reliability: float
    kind: str = "rss"


SOURCES: list[Source] = [
    # --- Stocks & Mutual Funds ---
    Source("Reuters Markets", "https://www.reutersagency.com/feed/?best-topics=business-finance", "stocks", 0.95),
    Source("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "stocks", 0.85),
    Source("MarketWatch Top", "http://feeds.marketwatch.com/marketwatch/topstories/", "stocks", 0.8),
    Source("Investing.com Stocks", "https://www.investing.com/rss/news_25.rss", "stocks", 0.7),

    # --- Commodities ---
    Source("CNBC Commodities", "https://www.cnbc.com/id/10000108/device/rss/rss.html", "commodities", 0.85),
    Source("Investing.com Commodities", "https://www.investing.com/rss/news_11.rss", "commodities", 0.7),
    Source("OilPrice.com", "https://oilprice.com/rss/main", "commodities", 0.75),

    # --- Artificial Intelligence ---
    Source("Google AI Blog", "https://blog.google/technology/ai/rss/", "ai", 0.9),
    Source("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed", "ai", 0.9),
    Source("VentureBeat AI", "https://venturebeat.com/category/ai/feed/", "ai", 0.75),
    Source("ArXiv cs.AI", "http://export.arxiv.org/rss/cs.AI", "ai", 0.85),

    # --- Semiconductors ---
    Source("AnandTech", "https://www.anandtech.com/rss/", "semiconductors", 0.85),
    Source("Tom's Hardware", "https://www.tomshardware.com/feeds/all", "semiconductors", 0.75),
    Source("EE Times", "https://www.eetimes.com/feed/", "semiconductors", 0.8),
    Source("SemiEngineering", "https://semiengineering.com/feed/", "semiconductors", 0.85),
]


def sources_for(domain: str) -> list[Source]:
    return [s for s in SOURCES if s.domain == domain]
