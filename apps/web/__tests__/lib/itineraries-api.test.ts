import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fetchMyItineraries,
  generateItinerary,
  ItineraryApiError,
  type ItineraryInput,
} from "@/lib/api/itineraries";

const BASE = "http://localhost:8000";

const input: ItineraryInput = {
  city_id: "874c6b46-de32-5014-8e54-da12587a7d7f",
  match_id: null,
  date: "2026-06-12",
  party_size: 2,
  interests: ["fan_zone", "food"],
  pace: "balanced",
};

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", BASE);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("itinerary API", () => {
  it("posts generation requests to the stub endpoint with auth", async () => {
    const body = {
      error: {
        code: "ITINERARY_GENERATION_NOT_IMPLEMENTED",
        message: "Itinerary generation is not implemented until Phase 06.",
      },
      meta: {},
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 501,
      json: () => Promise.resolve(body),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(generateItinerary(input, "token-1")).rejects.toMatchObject({
      status: 501,
      body,
    });

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/itineraries/generate`, {
      body: JSON.stringify(input),
      headers: {
        Authorization: "Bearer token-1",
        "Content-Type": "application/json",
      },
      method: "POST",
    });
  });

  it("loads saved itinerary history with pagination params", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          itineraries: [],
          pagination: { page: 2, page_size: 10, total_items: 0, total_pages: 0, has_next: false },
          meta: {},
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMyItineraries("token-1", 2, 10);

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/itineraries/me?page=2&page_size=10`, {
      headers: { Authorization: "Bearer token-1" },
    });
  });

  it("throws a structured error when history loading fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () =>
        Promise.resolve({
          error: { code: "UNAUTHORIZED", message: "Missing bearer token." },
          meta: {},
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchMyItineraries()).rejects.toBeInstanceOf(ItineraryApiError);
  });
});
