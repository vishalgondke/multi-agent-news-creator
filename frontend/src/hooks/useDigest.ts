import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { DomainKey } from "../types";

export function useDigest(domain: DomainKey) {
  return useQuery({
    queryKey: ["digest", domain],
    queryFn: () => api.digest(domain),
  });
}

export function useLatestVideo() {
  return useQuery({
    queryKey: ["video", "latest"],
    queryFn: () => api.latestVideo(),
    retry: false,
  });
}
