"""Pydantic response/request models for the API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ImpactOut(BaseModel):
    tickers: list[str] = []
    sentiment: str = "neutral"
    price_impact: str | None = None
    affected_cos: list[Any] = []
    confidence: float = 0.5


class DigestCard(BaseModel):
    summary_id: str
    headline: str
    bullets: list[str]
    deep_summary: str
    source_name: str
    source_url: str
    published_at: datetime | None = None
    impact: ImpactOut | None = None


class TrendOut(BaseModel):
    id: str
    domain: str
    title: str
    description: str
    momentum: str
    created_at: datetime


class DigestOut(BaseModel):
    id: str
    domain: str
    domain_label: str
    generated_at: datetime
    cards: list[DigestCard]
    trends: list[TrendOut] = []


class VideoOut(BaseModel):
    id: str
    status: str
    file_path: str | None = None
    duration_s: int | None = None
    script: str | None = None
    created_at: datetime


class RawItemOut(BaseModel):
    id: str
    domain: str
    title: str
    source_name: str
    source_url: str
    published_at: datetime | None = None
    collected_at: datetime
