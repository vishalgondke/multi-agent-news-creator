import type { Trend } from "../types";

const momentumIcon: Record<string, string> = {
  new: "✦",
  accelerating: "▲",
  plateauing: "▬",
  declining: "▼",
};

export function TrendBanner({ trends }: { trends: Trend[] }) {
  return (
    <div className="trend-banner">
      {trends.map((t) => (
        <div key={t.id} className="trend-pill" title={t.description}>
          <span className={`momentum momentum-${t.momentum}`}>
            {momentumIcon[t.momentum]}
          </span>
          <span className="trend-title">{t.title}</span>
        </div>
      ))}
    </div>
  );
}
