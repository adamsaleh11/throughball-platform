const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Hotspot = {
  hotspot_id: string;
  city_id: string;
  match_id: string | null;
  area_label: string;
  center: { lat: number; lng: number; precision: string };
  score: number;
  confidence: number;
  supporter_count: number;
  top_venue_ids: string[];
  ranking_factors: Record<string, unknown>;
  updated_at: string;
};

export type HotspotsResponse = {
  hotspots: Hotspot[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
  meta: {
    request_id: string;
    trace_id: string;
    latency_ms: number;
    retries: number;
    degraded: boolean;
  };
};

export type Match = {
  id: string;
  label?: string;
  title?: string;
  city_id?: string;
};

export type MatchesResponse = {
  matches: Match[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
  meta: {
    request_id: string;
    trace_id: string;
    latency_ms: number;
    retries: number;
    degraded: boolean;
  };
};

export async function fetchHotspots(
  cityId: string,
  matchId?: string
): Promise<HotspotsResponse> {
  const url = new URL(`${API_BASE_URL}/cities/${cityId}/hotspots`);
  if (matchId) url.searchParams.set("match_id", matchId);

  const response = await fetch(url.toString());
  if (!response.ok) throw new Error("Unable to load hotspots.");
  return response.json();
}

export async function fetchMatches(cityId: string): Promise<MatchesResponse> {
  const url = new URL(`${API_BASE_URL}/matches`);
  url.searchParams.set("city_id", cityId);

  const response = await fetch(url.toString());
  if (!response.ok) throw new Error("Unable to load matches.");
  return response.json();
}
