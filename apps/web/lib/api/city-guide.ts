const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ObservabilityMeta = {
  request_id: string;
  trace_id: string;
  latency_ms: number;
  retries: number;
  degraded: boolean;
};

export type Pagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next?: boolean;
};

export type City = {
  city_id: string;
  name: string;
  country_code: string;
  stadium_name?: string | null;
  timezone?: string | null;
};

export type CityDetailResponse = {
  city: City;
  meta: ObservabilityMeta;
};

export type MatchSummary = {
  match_id: string;
  city_id: string;
  home_team?: string | null;
  away_team?: string | null;
  competition: string;
  starts_at: string;
  status: string;
  tags: string[];
};

export type MatchesResponse = {
  matches: MatchSummary[];
  pagination: Pagination;
  meta: ObservabilityMeta;
};

export type Location = {
  lat: number | null;
  lng: number | null;
  precision: string | null;
};

export type SourceBackedRecord = {
  source_name: string;
  source_url: string;
  data_origin: string;
  last_verified_at: string;
};

export type Venue = SourceBackedRecord & {
  venue_id: string;
  city_id: string;
  name: string;
  venue_type: string;
  area_label?: string | null;
  location: Location;
  capacity_estimate?: number | null;
  amenities: string[];
  tags: string[];
};

export type CityEvent = SourceBackedRecord & {
  event_id: string;
  city_id: string;
  title: string;
  event_type: string;
  area_label?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  tags: string[];
};

export type TouristSpot = SourceBackedRecord & {
  spot_id: string;
  city_id: string;
  name: string;
  spot_type: string;
  area_label?: string | null;
  location: Location;
  tags: string[];
};

export type VenuesResponse = {
  venues: Venue[];
  pagination: Pagination;
  meta: ObservabilityMeta;
};

export type CityEventsResponse = {
  events: CityEvent[];
  pagination: Pagination;
  meta: ObservabilityMeta;
};

export type TouristSpotsResponse = {
  tourist_spots: TouristSpot[];
  pagination: Pagination;
  meta: ObservabilityMeta;
};

export type EventFilters = {
  startsAfter?: string;
  startsBefore?: string;
  pageSize?: number;
};

async function getJson<TResponse>(url: URL | string, errorMessage: string): Promise<TResponse> {
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(errorMessage);
  return response.json();
}

export function fetchCity(cityId: string): Promise<CityDetailResponse> {
  return getJson(`${API_BASE_URL}/cities/${cityId}`, "Unable to load city.");
}

export function fetchCityMatches(cityId: string): Promise<MatchesResponse> {
  const url = new URL(`${API_BASE_URL}/matches`);
  url.searchParams.set("city_id", cityId);
  return getJson(url, "Unable to load city matches.");
}

export function fetchCityVenues(cityId: string): Promise<VenuesResponse> {
  return getJson(`${API_BASE_URL}/cities/${cityId}/venues`, "Unable to load venues.");
}

export function fetchCityEvents(
  cityId: string,
  filters: EventFilters = {}
): Promise<CityEventsResponse> {
  const url = new URL(`${API_BASE_URL}/cities/${cityId}/events`);
  if (filters.startsAfter) url.searchParams.set("starts_after", filters.startsAfter);
  if (filters.startsBefore) url.searchParams.set("starts_before", filters.startsBefore);
  if (filters.pageSize) url.searchParams.set("page_size", String(filters.pageSize));
  return getJson(url, "Unable to load city events.");
}

export function fetchCityTouristSpots(cityId: string): Promise<TouristSpotsResponse> {
  return getJson(`${API_BASE_URL}/cities/${cityId}/tourist-spots`, "Unable to load tourist spots.");
}
