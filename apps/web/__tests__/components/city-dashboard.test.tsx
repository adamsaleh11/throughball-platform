import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CityDashboard } from "@/components/cities/city-dashboard";
import { DEFAULT_CITY_ID } from "@/lib/city-dashboard";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

const TORONTO_ID = DEFAULT_CITY_ID;

function meta() {
  return {
    request_id: "req-1",
    trace_id: "trace-1",
    latency_ms: 10,
    retries: 0,
    degraded: false,
  };
}

function city(timezone: string | null = "America/Toronto") {
  return {
    city_id: TORONTO_ID,
    name: "Toronto",
    country_code: "CA",
    stadium_name: "BMO Field",
    timezone,
  };
}

function responseFor(url: string) {
  if (url.endsWith(`/cities/${TORONTO_ID}`)) {
    return { city: city(), meta: meta() };
  }
  if (url.endsWith(`/matches?city_id=${TORONTO_ID}`)) {
    return {
      matches: [
        {
          match_id: "match-1",
          city_id: TORONTO_ID,
          home_team: "Canada",
          away_team: "Mexico",
          competition: "FIFA World Cup 2026",
          starts_at: "2026-06-12T23:00:00Z",
          status: "scheduled",
          tags: ["world-cup"],
        },
      ],
      pagination: pagination(1),
      meta: meta(),
    };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/hotspots`)) {
    return {
      hotspots: [
        {
          hotspot_id: "hotspot-1",
          city_id: TORONTO_ID,
          match_id: null,
          area_label: "Liberty Village",
          center: { lat: 43.64, lng: -79.42, precision: "neighbourhood" },
          score: 84,
          confidence: 0.88,
          supporter_count: 240,
          top_venue_ids: [],
          ranking_factors: {},
          updated_at: "2026-06-12T20:00:00Z",
        },
      ],
      pagination: pagination(1),
      meta: meta(),
    };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/venues`)) {
    return {
      venues: [
        {
          venue_id: "venue-1",
          city_id: TORONTO_ID,
          name: "Cafe Diplomatico",
          venue_type: "bar",
          area_label: "Little Italy",
          location: { lat: 43.65, lng: -79.41, precision: "address" },
          capacity_estimate: null,
          amenities: ["screens"],
          tags: ["football"],
          source_name: "City source",
          source_url: "https://example.com/venue",
          data_origin: "seed",
          last_verified_at: "2026-05-01T00:00:00Z",
        },
      ],
      pagination: pagination(1),
      meta: meta(),
    };
  }
  if (url.includes(`/cities/${TORONTO_ID}/events`)) {
    return {
      events: [
        {
          event_id: "event-1",
          city_id: TORONTO_ID,
          title: "Waterfront watch party",
          event_type: "watch_party",
          area_label: "Waterfront",
          starts_at: "2026-06-13T00:00:00Z",
          ends_at: null,
          tags: ["world-cup"],
          source_name: "Tourism source",
          source_url: "https://example.com/event",
          data_origin: "seed",
          last_verified_at: "2026-05-01T00:00:00Z",
        },
      ],
      pagination: pagination(1),
      meta: meta(),
    };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/tourist-spots`)) {
    return {
      tourist_spots: [
        {
          spot_id: "spot-1",
          city_id: TORONTO_ID,
          name: "CN Tower",
          spot_type: "landmark",
          area_label: "Downtown",
          location: { lat: 43.64, lng: -79.38, precision: "address" },
          tags: ["landmark"],
          source_name: "Tourism source",
          source_url: "https://example.com/spot",
          data_origin: "seed",
          last_verified_at: "2026-05-01T00:00:00Z",
        },
      ],
      pagination: pagination(1),
      meta: meta(),
    };
  }
  throw new Error(`Unexpected URL: ${url}`);
}

function emptyResponseFor(url: string) {
  if (url.endsWith(`/cities/${TORONTO_ID}`)) return { city: city(), meta: meta() };
  if (url.endsWith(`/matches?city_id=${TORONTO_ID}`)) {
    return { matches: [], pagination: pagination(0), meta: meta() };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/hotspots`)) {
    return { hotspots: [], pagination: pagination(0), meta: meta() };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/venues`)) {
    return { venues: [], pagination: pagination(0), meta: meta() };
  }
  if (url.includes(`/cities/${TORONTO_ID}/events`)) {
    return { events: [], pagination: pagination(0), meta: meta() };
  }
  if (url.endsWith(`/cities/${TORONTO_ID}/tourist-spots`)) {
    return { tourist_spots: [], pagination: pagination(0), meta: meta() };
  }
  throw new Error(`Unexpected URL: ${url}`);
}

function pagination(totalItems: number) {
  return {
    page: 1,
    page_size: 20,
    total_items: totalItems,
    total_pages: totalItems ? 1 : 0,
    has_next: false,
  };
}

function renderDashboard(fetchMock = defaultFetchMock(), cityId = TORONTO_ID) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  vi.stubGlobal("fetch", fetchMock);

  return render(
    <QueryClientProvider client={queryClient}>
      <CityDashboard cityId={cityId} />
    </QueryClientProvider>
  );
}

function defaultFetchMock() {
  return vi.fn().mockImplementation((url: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(responseFor(url)),
    })
  );
}

beforeEach(() => {
  vi.setSystemTime(new Date("2026-06-12T16:00:00.000Z"));
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("CityDashboard", () => {
  it("renders API-backed city sections", async () => {
    renderDashboard();

    expect(await screen.findByRole("heading", { name: "Toronto" })).toBeInTheDocument();
    expect(await screen.findByText("Canada vs Mexico")).toBeInTheDocument();
    expect(await screen.findByText("Liberty Village")).toBeInTheDocument();
    expect(await screen.findByText("Cafe Diplomatico")).toBeInTheDocument();
    expect(await screen.findByText("Waterfront watch party")).toBeInTheDocument();
    expect(await screen.findByText("CN Tower")).toBeInTheDocument();
  });

  it("renders empty states independently", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(emptyResponseFor(url)),
      })
    );

    renderDashboard(fetchMock);

    expect(await screen.findByText("No matches yet")).toBeInTheDocument();
    expect(screen.getByText("No hotspots yet")).toBeInTheDocument();
    expect(screen.getByText("No venues yet")).toBeInTheDocument();
    expect(screen.getByText("No events tonight")).toBeInTheDocument();
    expect(screen.getByText("No tourist spots yet")).toBeInTheDocument();
  });

  it("does not call city APIs for invalid route city IDs", async () => {
    const fetchMock = defaultFetchMock();

    renderDashboard(fetchMock, "not-a-city");

    expect(screen.getByText("City not found")).toBeInTheDocument();
    expect(screen.getByText("Toronto")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("distinguishes a known-city fetch failure from an invalid city", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({}),
    });

    renderDashboard(fetchMock);

    expect(await screen.findByText("Could not load city")).toBeInTheDocument();
    expect(screen.queryByText("City not found")).not.toBeInTheDocument();
  });

  it("queries events using a city-timezone tonight window", async () => {
    const fetchMock = defaultFetchMock();

    renderDashboard(fetchMock);

    await screen.findByText("Waterfront watch party");

    await waitFor(() => {
      const eventsUrl = fetchMock.mock.calls.map((call) => call[0] as string).find((url) => url.includes("/events?"));
      expect(eventsUrl).toContain("starts_after=2026-06-12T22%3A00%3A00.000Z");
      expect(eventsUrl).toContain("starts_before=2026-06-13T10%3A00%3A00.000Z");
    });
  });

  it("does not query events when city timezone is missing", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith(`/cities/${TORONTO_ID}`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ city: city(null), meta: meta() }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(emptyResponseFor(url)),
      });
    });

    renderDashboard(fetchMock);

    expect(await screen.findByText("Event timing unavailable")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((call) => (call[0] as string).includes("/events"))).toBe(false);
  });

  it("keeps the AI concierge entry local on load and click", async () => {
    const user = userEvent.setup();
    const fetchMock = defaultFetchMock();

    renderDashboard(fetchMock);

    await screen.findByRole("heading", { name: "Toronto" });
    await screen.findByRole("button", { name: /open/i });
    const callsAfterLoad = fetchMock.mock.calls.length;

    await user.click(screen.getByRole("button", { name: /open/i }));

    expect(screen.getByText("Concierge ready for Phase 06")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(callsAfterLoad);
  });
});
