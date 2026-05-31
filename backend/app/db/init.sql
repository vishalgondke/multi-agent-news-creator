-- MySQL 8 schema for Market & Tech News Content Creator
-- Applied automatically by docker-entrypoint when the container is first created.

CREATE DATABASE IF NOT EXISTS marketnews
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE marketnews;

-- Raw collected items ------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_items (
    id            CHAR(36)     NOT NULL PRIMARY KEY,
    domain        VARCHAR(32)  NOT NULL,           -- stocks|commodities|ai|semiconductors
    source_url    TEXT         NOT NULL,
    source_name   VARCHAR(255) NOT NULL,
    content_hash  CHAR(64)     NOT NULL,           -- dedup key (sha256)
    title         TEXT         NOT NULL,
    body          MEDIUMTEXT,
    published_at  DATETIME     NULL,
    collected_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reliability   DECIMAL(3,2) NOT NULL DEFAULT 0.50,
    UNIQUE KEY uq_raw_hash (content_hash),
    KEY idx_raw_domain_time (domain, collected_at)
) ENGINE=InnoDB;

-- Story clusters -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS clusters (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    domain      VARCHAR(32)  NOT NULL,
    label       TEXT         NOT NULL,
    embedding   JSON         NULL,                 -- MySQL has no native vector type; store array
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_cluster_domain (domain)
) ENGINE=InnoDB;

-- Processed summaries ------------------------------------------------------
CREATE TABLE IF NOT EXISTS summaries (
    id            CHAR(36)     NOT NULL PRIMARY KEY,
    raw_item_id   CHAR(36)     NOT NULL,
    domain        VARCHAR(32)  NOT NULL,
    headline      TEXT         NOT NULL,
    bullets       JSON         NOT NULL,           -- ["b1","b2","b3"]
    deep_summary  MEDIUMTEXT   NOT NULL,
    cluster_id    CHAR(36)     NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_sum_domain_time (domain, created_at),
    KEY idx_sum_raw (raw_item_id),
    CONSTRAINT fk_sum_raw    FOREIGN KEY (raw_item_id) REFERENCES raw_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_sum_cluster FOREIGN KEY (cluster_id) REFERENCES clusters(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Trend analysis -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS trends (
    id           CHAR(36)     NOT NULL PRIMARY KEY,
    domain       VARCHAR(32)  NOT NULL,
    title        TEXT         NOT NULL,
    description  MEDIUMTEXT   NOT NULL,
    momentum     ENUM('new','accelerating','plateauing','declining') NOT NULL DEFAULT 'new',
    period_start DATETIME     NOT NULL,
    period_end   DATETIME     NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_trend_domain_time (domain, created_at)
) ENGINE=InnoDB;

-- Impact assessments -------------------------------------------------------
CREATE TABLE IF NOT EXISTS impact_assessments (
    id           CHAR(36)     NOT NULL PRIMARY KEY,
    summary_id   CHAR(36)     NOT NULL,
    tickers      JSON         NULL,                -- ["AAPL","NVDA"]
    sentiment    ENUM('positive','negative','neutral') NOT NULL DEFAULT 'neutral',
    price_impact TEXT         NULL,
    affected_cos JSON         NULL,
    confidence   DECIMAL(3,2) NOT NULL DEFAULT 0.50,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_impact_summary (summary_id),
    CONSTRAINT fk_impact_sum FOREIGN KEY (summary_id) REFERENCES summaries(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Generated digests (what the frontend reads) ------------------------------
CREATE TABLE IF NOT EXISTS digests (
    id           CHAR(36)     NOT NULL PRIMARY KEY,
    domain       VARCHAR(32)  NOT NULL,
    content      JSON         NOT NULL,            -- full digest payload
    generated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_digest_domain_time (domain, generated_at)
) ENGINE=InnoDB;

-- Video generations --------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    script      MEDIUMTEXT   NOT NULL,
    file_path   TEXT         NULL,                 -- local path or S3 url
    duration_s  INT          NULL,
    status      ENUM('pending','processing','done','failed') NOT NULL DEFAULT 'pending',
    error       TEXT         NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_video_time (created_at)
) ENGINE=InnoDB;

-- Pipeline run audit log ---------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id           CHAR(36)     NOT NULL PRIMARY KEY,
    started_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at  DATETIME     NULL,
    status       ENUM('running','success','failed') NOT NULL DEFAULT 'running',
    stats        JSON         NULL,
    error        TEXT         NULL
) ENGINE=InnoDB;
