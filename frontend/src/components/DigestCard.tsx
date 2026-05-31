import { useState } from "react";
import type { DigestCard as Card } from "../types";

const sentimentColor: Record<string, string> = {
  positive: "#1f9d55",
  negative: "#e3342f",
  neutral: "#8795a1",
};

export function DigestCard({ card }: { card: Card }) {
  const [open, setOpen] = useState(false);
  const impact = card.impact;

  return (
    <article className="card">
      <h3 className="card-headline">{card.headline}</h3>

      <ul className="bullets">
        {card.bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>

      {impact && (
        <div className="impact-row">
          <span
            className="chip"
            style={{ background: sentimentColor[impact.sentiment] }}
          >
            {impact.sentiment}
          </span>
          {impact.tickers.map((t) => (
            <span key={t} className="ticker">
              {t}
            </span>
          ))}
          {impact.confidence > 0 && (
            <span className="confidence">
              {Math.round(impact.confidence * 100)}% conf.
            </span>
          )}
        </div>
      )}

      <button className="link-btn" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide analysis" : "Read analysis"}
      </button>

      {open && (
        <div className="deep">
          <p>{card.deep_summary}</p>
          {impact?.price_impact && (
            <p className="price-impact">
              <strong>Market impact:</strong> {impact.price_impact}
            </p>
          )}
        </div>
      )}

      <div className="card-foot">
        <a href={card.source_url} target="_blank" rel="noreferrer">
          {card.source_name} ↗
        </a>
        {card.published_at && (
          <span className="dim">
            {new Date(card.published_at).toLocaleDateString()}
          </span>
        )}
      </div>
    </article>
  );
}
