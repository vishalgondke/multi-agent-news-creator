import type { DomainKey } from "../types";

interface Props {
  domains: { key: DomainKey; label: string }[];
  active: DomainKey;
  onSelect: (d: DomainKey) => void;
}

export function TabNav({ domains, active, onSelect }: Props) {
  return (
    <nav className="tabnav">
      {domains.map((d) => (
        <button
          key={d.key}
          className={`tab ${active === d.key ? "tab-active" : ""}`}
          onClick={() => onSelect(d.key)}
        >
          {d.label}
        </button>
      ))}
    </nav>
  );
}
