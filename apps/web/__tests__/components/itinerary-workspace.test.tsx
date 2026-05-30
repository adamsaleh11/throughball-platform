import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ItineraryWorkspace } from "@/components/itineraries/itinerary-workspace";
import type { Itinerary } from "@/lib/api/itineraries";

let searchParams = new URLSearchParams();
const pushMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
  useSearchParams: () => searchParams,
}));

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: vi.fn(),
  isSupabaseConfigured: () => false,
}));

const cityId = "874c6b46-de32-5014-8e54-da12587a7d7f";
const matchId = "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101";

function meta() {
  return {
    request_id: "req-1",
    trace_id: "trace-1",
    latency_ms: 12,
    retries: 0,
    degraded: false,
  };
}

function savedItinerary(overrides: Partial<Itinerary> = {}): Itinerary {
  return {
    itinerary_id: "itin-1",
    city_id: cityId,
    match_id: null,
    input_hash: "sha256:abc",
    input: {
      city_id: cityId,
      match_id: null,
      date: "2026-06-12",
      party_size: 2,
      interests: ["food", "fan_zone"],
      pace: "balanced",
    },
    title: "Match Day in Toronto",
    summary: "A compact saved plan.",
    status: "saved",
    items: [
      {
        item_id: "item-1",
        position: 1,
        item_type: "venue",
        source_table: "venues",
        source_id: "22222222-2222-4222-8222-222222222222",
        title: "BMO Field",
        description: "Arrive early around Exhibition Place.",
        starts_at: "2026-06-12T16:00:00Z",
        ends_at: "2026-06-12T18:00:00Z",
        area_label: "Exhibition Place",
        route_context: {
          from_previous_label: "Union Station",
          approx_minutes: 18,
          mode: "transit",
        },
      },
    ],
    created_at: "2026-05-28T18:00:00Z",
    updated_at: "2026-05-28T18:00:00Z",
    ...overrides,
  };
}

function responseFor(url: string, itineraries: Itinerary[] = []) {
  if (url.includes("/itineraries/me")) {
    return {
      itineraries,
      pagination: {
        page: 1,
        page_size: 20,
        total_items: itineraries.length,
        total_pages: itineraries.length ? 1 : 0,
        has_next: false,
      },
      meta: meta(),
    };
  }
  if (url.includes(`/matches?city_id=${cityId}`)) {
    return {
      matches: [
        {
          match_id: matchId,
          city_id: cityId,
          home_team: "Canada",
          away_team: "Mexico",
          competition: "FIFA World Cup 2026",
          starts_at: "2026-06-12T23:00:00Z",
          status: "scheduled",
          tags: ["world-cup"],
        },
      ],
      pagination: { page: 1, page_size: 20, total_items: 1, total_pages: 1, has_next: false },
      meta: meta(),
    };
  }
  throw new Error(`Unexpected URL: ${url}`);
}

function renderWorkspace(fetchMock: ReturnType<typeof vi.fn>) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  vi.stubGlobal("fetch", fetchMock);

  return render(
    <QueryClientProvider client={queryClient}>
      <ItineraryWorkspace />
    </QueryClientProvider>
  );
}

function defaultFetchMock(itineraries: Itinerary[] = []) {
  return vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    if (url.endsWith("/itineraries/generate")) {
      return Promise.resolve({
        ok: false,
        status: 501,
        json: () =>
          Promise.resolve({
            error: {
              code: "ITINERARY_GENERATION_NOT_IMPLEMENTED",
              message: "Itinerary generation is not implemented until Phase 06.",
              details: { phase: "Phase 06" },
            },
            meta: meta(),
          }),
      });
    }

    if (options?.method === "POST") throw new Error(`Unexpected POST: ${url}`);

    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(responseFor(url, itineraries)),
    });
  });
}

beforeEach(() => {
  vi.setSystemTime(new Date("2026-06-12T16:00:00.000Z"));
  searchParams = new URLSearchParams();
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: {
      writeText: vi.fn().mockResolvedValue(undefined),
    },
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("ItineraryWorkspace", () => {
  it("loads saved itineraries without generating on page load", async () => {
    const fetchMock = defaultFetchMock();

    renderWorkspace(fetchMock);

    expect(await screen.findByRole("heading", { name: "Itineraries" })).toBeInTheDocument();
    expect(await screen.findByText("No saved itineraries")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/itineraries/generate"))).toBe(false);
  });

  it("submits the form to the generation stub on explicit generate", async () => {
    const user = userEvent.setup();
    const fetchMock = defaultFetchMock();

    renderWorkspace(fetchMock);

    await screen.findByText("No saved itineraries");
    await user.click(screen.getByRole("button", { name: "Generate" }));

    expect(await screen.findByText("Generation staged for Phase 06")).toBeInTheDocument();
    const generateCall = fetchMock.mock.calls.find((call) => String(call[0]).includes("/itineraries/generate"));
    expect(generateCall).toBeTruthy();
    expect(JSON.parse(String(generateCall?.[1]?.body))).toMatchObject({
      city_id: cityId,
      date: "2026-06-12",
      party_size: 2,
      interests: ["fan_zone", "food"],
      pace: "balanced",
    });
  });

  it("prevents duplicate generation for the same submitted input", async () => {
    const user = userEvent.setup();
    const fetchMock = defaultFetchMock();

    renderWorkspace(fetchMock);

    await screen.findByText("No saved itineraries");
    await user.click(screen.getByRole("button", { name: "Generate" }));
    await screen.findByText("Generation staged for Phase 06");
    await user.click(screen.getByRole("button", { name: "Generate" }));

    const generateCalls = fetchMock.mock.calls.filter((call) => String(call[0]).includes("/itineraries/generate"));
    expect(generateCalls).toHaveLength(1);
  });

  it("renders and selects saved itinerary details with route context", async () => {
    const user = userEvent.setup();
    const fetchMock = defaultFetchMock([savedItinerary()]);

    renderWorkspace(fetchMock);

    await screen.findByText("Matching saved itinerary: Match Day in Toronto");
    await user.click(screen.getByRole("button", { name: /Match Day in Toronto/i }));

    expect(await screen.findByRole("heading", { name: "Match Day in Toronto" })).toBeInTheDocument();
    expect(screen.getByText("Arrive early around Exhibition Place.")).toBeInTheDocument();
    expect(screen.getByText(/From Union Station/)).toBeInTheDocument();
    expect(screen.getByText("Exhibition Place")).toBeInTheDocument();
  });

  it("focuses query-selected itineraries and copies private share URLs", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    searchParams = new URLSearchParams("itinerary=itin-1");
    const fetchMock = defaultFetchMock([savedItinerary()]);

    renderWorkspace(fetchMock);

    expect(await screen.findByRole("heading", { name: "Match Day in Toronto" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Share" }));

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        expect.stringContaining("/app/itineraries?itinerary=itin-1")
      )
    );
  });

  it("handles stale shared itinerary links gracefully", async () => {
    searchParams = new URLSearchParams("itinerary=missing-id");
    const fetchMock = defaultFetchMock([savedItinerary()]);

    renderWorkspace(fetchMock);

    expect(await screen.findByText("The shared itinerary link is not in your saved history.")).toBeInTheDocument();
    expect(screen.getByText("Select an itinerary")).toBeInTheDocument();
  });
});
