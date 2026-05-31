import type { Digest, DomainKey, Video } from "../types";

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  digest: (domain: DomainKey) => get<Digest>(`/v1/digests/${domain}`),
  allDigests: () => get<Record<DomainKey, Digest | null>>(`/v1/digests/all`),
  latestVideo: () => get<Video>(`/v1/videos/latest`),
  generateVideo: async () => {
    const res = await fetch(`/v1/videos/generate`, { method: "POST" });
    return res.json();
  },
};
