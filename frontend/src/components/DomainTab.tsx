import { useDigest } from "../hooks/useDigest";
import type { DomainKey } from "../types";
import { DigestCard } from "./DigestCard";
import { TrendBanner } from "./TrendBanner";

export function DomainTab({ domain }: { domain: DomainKey }) {
  const { data, isLoading, isError, error } = useDigest(domain);

  if (isLoading) return <div className="state">Loading latest digest…</div>;
  if (isError)
    return (
      <div className="state state-error">
        <p>No digest available yet for this domain.</p>
        <p className="hint">
          Run the pipeline once on the backend:{" "}
          <code>python -m app.orchestration.run_once</code>
        </p>
        <p className="dim">{(error as Error)?.message}</p>
      </div>
    );
  if (!data) return null;

  return (
    <div>
      <div className="digest-head">
        <h2>{data.domain_label}</h2>
        <span className="updated">
          Updated {new Date(data.generated_at).toLocaleString()}
        </span>
      </div>

      {data.trends?.length > 0 && <TrendBanner trends={data.trends} />}

      <div className="grid">
        {data.cards.map((card) => (
          <DigestCard key={card.summary_id} card={card} />
        ))}
      </div>

      {data.cards.length === 0 && (
        <div className="state">No stories collected in the latest run.</div>
      )}
    </div>
  );
}
