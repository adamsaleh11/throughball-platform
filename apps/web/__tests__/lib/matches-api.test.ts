import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fetchMatch,
  fetchMatchEvents,
  fetchMatchMomentum,
  fetchMatchStats,
} from "@/lib/api/matches";

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

describe("match API client", () => {
  it("loads match detail from the match endpoint", async () => {
    const fetchMock = mockFetch({ match: {}, meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMatch("match-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/matches/match-123`);
  });

  it("loads match stats from the stats endpoint", async () => {
    const fetchMock = mockFetch({ stats: [], meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMatchStats("match-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/matches/match-123/stats`);
  });

  it("loads match events from the events endpoint", async () => {
    const fetchMock = mockFetch({ events: [], meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMatchEvents("match-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/matches/match-123/events`);
  });

  it("loads match momentum from the momentum endpoint", async () => {
    const fetchMock = mockFetch({ momentum: [], meta: {} });
    vi.stubGlobal("fetch", fetchMock);

    await fetchMatchMomentum("match-123");

    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/matches/match-123/momentum`);
  });

  it("throws a clear error when a match request fails", async () => {
    const fetchMock = mockFetch({}, false);
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchMatch("missing-match")).rejects.toThrow("Unable to load match.");
  });
});
