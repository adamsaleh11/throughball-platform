import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchHotspots, fetchMatches } from "@/lib/api/fan";

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
  vi.restoreAllMocks();
});

describe("fetchHotspots", () => {
  it("calls the correct URL without match_id", async () => {
    const fetchMock = mockFetch({ hotspots: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchHotspots("city-123");

    expect(fetchMock).toHaveBeenCalledOnce();
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe(`${BASE}/cities/city-123/hotspots`);
  });

  it("appends match_id when provided", async () => {
    const fetchMock = mockFetch({ hotspots: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchHotspots("city-123", "match-456");

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe(`${BASE}/cities/city-123/hotspots?match_id=match-456`);
  });

  it("does not append match_id when undefined", async () => {
    const fetchMock = mockFetch({ hotspots: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchHotspots("city-123", undefined);

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).not.toContain("match_id");
  });

  it("throws when response is not ok", async () => {
    const fetchMock = mockFetch({}, false);
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchHotspots("city-123")).rejects.toThrow("Unable to load hotspots.");
  });
});

describe("fetchMatches", () => {
  it("calls the correct URL with city_id as a query param", async () => {
    const fetchMock = mockFetch({ matches: [], pagination: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMatches("city-789");

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe(`${BASE}/matches?city_id=city-789`);
  });

  it("throws when response is not ok", async () => {
    const fetchMock = mockFetch({}, false);
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchMatches("city-789")).rejects.toThrow("Unable to load matches.");
  });
});
