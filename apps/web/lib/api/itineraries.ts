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
  has_next: boolean;
};

export type ItineraryInput = {
  city_id: string;
  match_id: string | null;
  date: string | null;
  party_size: number;
  interests: string[];
  pace: string;
};

export type ItineraryItem = {
  item_id: string;
  position: number;
  item_type: string;
  source_table: string | null;
  source_id: string | null;
  title: string;
  description: string | null;
  starts_at: string | null;
  ends_at: string | null;
  area_label: string | null;
  route_context: Record<string, unknown>;
};

export type Itinerary = {
  itinerary_id: string;
  city_id: string;
  match_id: string | null;
  input_hash: string;
  input: ItineraryInput;
  title: string;
  summary: string | null;
  status: string;
  items: ItineraryItem[];
  created_at: string;
  updated_at: string;
};

export type GenerateItineraryStubResponse = {
  error: {
    code: "ITINERARY_GENERATION_NOT_IMPLEMENTED" | string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta: ObservabilityMeta;
};

export type MyItinerariesResponse = {
  itineraries: Itinerary[];
  pagination: Pagination;
  meta: ObservabilityMeta;
};

export class ItineraryApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, fallbackMessage: string) {
    const message =
      typeof body === "object" &&
      body !== null &&
      "error" in body &&
      typeof body.error === "object" &&
      body.error !== null &&
      "message" in body.error &&
      typeof body.error.message === "string"
        ? body.error.message
        : fallbackMessage;
    super(message);
    this.name = "ItineraryApiError";
    this.status = status;
    this.body = body;
  }
}

function authHeaders(accessToken?: string | null): HeadersInit {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

async function parseJsonResponse(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

export async function generateItinerary(
  input: ItineraryInput,
  accessToken?: string | null
): Promise<never> {
  const response = await fetch(`${API_BASE_URL}/itineraries/generate`, {
    body: JSON.stringify(input),
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(accessToken),
    },
    method: "POST",
  });
  const body = await parseJsonResponse(response);
  throw new ItineraryApiError(response.status, body, "Unable to generate itinerary.");
}

export async function fetchMyItineraries(
  accessToken?: string | null,
  page = 1,
  pageSize = 20
): Promise<MyItinerariesResponse> {
  const url = new URL(`${API_BASE_URL}/itineraries/me`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("page_size", String(pageSize));

  const response = await fetch(url.toString(), {
    headers: authHeaders(accessToken),
  });
  const body = await parseJsonResponse(response);
  if (!response.ok) {
    throw new ItineraryApiError(response.status, body, "Unable to load itineraries.");
  }
  return body as MyItinerariesResponse;
}
