"""SQLAlchemy ORM models mapped to the MySQL schema in app/db/init.sql."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class RawItem(Base):
    __tablename__ = "raw_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    source_name: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reliability: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.50)


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    raw_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("raw_items.id", ondelete="CASCADE"))
    domain: Mapped[str] = mapped_column(String(32), index=True)
    headline: Mapped[str] = mapped_column(Text)
    bullets: Mapped[list] = mapped_column(JSON)
    deep_summary: Mapped[str] = mapped_column(Text)
    cluster_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Trend(Base):
    __tablename__ = "trends"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    momentum: Mapped[str] = mapped_column(
        Enum("new", "accelerating", "plateauing", "declining"), default="new"
    )
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    summary_id: Mapped[str] = mapped_column(String(36), ForeignKey("summaries.id", ondelete="CASCADE"))
    tickers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[str] = mapped_column(
        Enum("positive", "negative", "neutral"), default="neutral"
    )
    price_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_cos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.50)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    script: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "done", "failed"), default="pending"
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("running", "success", "failed"), default="running"
    )
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
