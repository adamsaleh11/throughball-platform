import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fetchCity,
  fetchCityEvents,
  fetchCityMatches,
  fetchCityTouristSpots,
  fetchCityVenues,
} from "@/lib/api/city-guide";

const BASE = "http://localhost:8000";

function mockFetch(body: unknown, ok = true) {
  return vi.fn().mockResolvedValue({
    ok,
    json: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", BASE);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("city guide API", () => {
  it("fetches city detail from the city-scoped route", async () => {
    const fetchMock = mockFetch({ city: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchCity("city-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/cities/city-123`);
  });

  it("fetches matches with city_id as a query param", async () => {
    const fetchMock = mockFetch({ matches: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchCityMatches("city-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/matches?city_id=city-123`);
  });

  it("fetches venues and tourist spots from city-scoped routes", async () => {
    const fetchMock = mockFetch({ venues: [], tourist_spots: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchCityVenues("city-123");
    await fetchCityTouristSpots("city-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/cities/city-123/venues`);
    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/cities/city-123/tourist-spots`);
  });

  it("adds event date filters when provided", async () => {
    const fetchMock = mockFetch({ events: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchCityEvents("city-123", {
      startsAfter: "2026-06-12T22:00:00.000Z",
      startsBefore: "2026-06-13T10:00:00.000Z",
      pageSize: 6,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${BASE}/cities/city-123/events?starts_after=2026-06-12T22%3A00%3A00.000Z&starts_before=2026-06-13T10%3A00%3A00.000Z&page_size=6`
    );
  });

  it("throws when a response is not ok", async () => {
    const fetchMock = mockFetch({}, false);
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchCityVenues("city-123")).rejects.toThrow("Unable to load venues.");
  });
});
