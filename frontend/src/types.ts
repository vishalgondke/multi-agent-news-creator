export type DomainKey = "stocks" | "commodities" | "ai" | "semiconductors";

export interface Impact {
  tickers: string[];
  sentiment: "positive" | "negative" | "neutral";
  price_impact: string | null;
  affected_cos: string[];
  confidence: number;
}

export interface DigestCard {
  summary_id: string;
  headline: string;
  bullets: string[];
  deep_summary: string;
  source_name: string;
  source_url: string;
  published_at: string | null;
  impact: Impact | null;
}

export interface Trend {
  id: string;
  domain: string;
  title: string;
  description: string;
  momentum: "new" | "accelerating" | "plateauing" | "declining";
  created_at: string;
}

export interface Digest {
  id: string;
  domain: DomainKey;
  domain_label: string;
  generated_at: string;
  cards: DigestCard[];
  trends: Trend[];
}

export interface Video {
  id: string;
  status: string;
  file_path: string | null;
  media_url: string | null;
  duration_s: number | null;
  script: string | null;
  created_at: string;
}
