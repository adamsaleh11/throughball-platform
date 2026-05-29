import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MatchDashboard, deriveScoreline } from "@/components/matches/match-dashboard";
import type { MatchDetail, MatchStat } from "@/lib/api/matches";

const matchId = "match-123";

const match: MatchDetail = {
  match_id: matchId,
  city: {
    city_id: "city-toronto",
    name: "Toronto",
    country_code: "CA",
    stadium_name: "BMO Field",
    timezone: "America/Toronto",
  },
  home_team: {
    team_id: "team-canada",
    name: "Canada",
    country_code: "CA",
  },
  away_team: {
    team_id: "team-mexico",
    name: "Mexico",
    country_code: "MX",
  },
  competition: "FIFA World Cup 2026",
  stage: "group_stage",
  starts_at: "2026-06-12T23:00:00Z",
  status: "scheduled",
  tags: ["world-cup", "group-stage", "toronto"],
};

const stats: MatchStat[] = [
  {
    team_id: "team-canada",
    team_name: "Canada",
    goals: 3,
    possession_pct: 48.5,
    shots: 11,
    shots_on_target: 4,
    passes: 435,
    corners: 5,
    fouls: 12,
  },
  {
    team_id: "team-mexico",
    team_name: "Mexico",
    goals: 0,
    possession_pct: 51.5,
    shots: 13,
    shots_on_target: 5,
    passes: 472,
    corners: 6,
    fouls: 10,
  },
];

function responseFor(url: string) {
  if (url.endsWith(`/matches/${matchId}`)) {
    return { match, meta: meta() };
  }
  if (url.endsWith(`/matches/${matchId}/stats`)) {
    return { stats, meta: meta() };
  }
  if (url.endsWith(`/matches/${matchId}/events`)) {
    return {
      events: [
        {
          event_id: "event-1",
          team_id: "team-mexico",
          team_name: "Mexico",
          player_id: null,
          player_name: null,
          event_type: "yellow_card",
          minute: 42,
          stoppage_minute: null,
          description: "Booked for stopping a transition.",
        },
      ],
      meta: meta(),
    };
  }
  if (url.endsWith(`/matches/${matchId}/momentum`)) {
    return {
      momentum: [
        {
          snapshot_id: "snapshot-1",
          team_id: "team-canada",
          team_name: "Canada",
          minute: 15,
          formation: "3-4-2-1",
          possession_style: "direct wide progression",
          press_intensity: "high",
          defensive_line: "mid",
          confidence: 0.82,
        },
      ],
      meta: meta(),
    };
  }
  throw new Error(`Unexpected URL: ${url}`);
}

function meta() {
  return {
    request_id: "req-1",
    trace_id: "trace-1",
    latency_ms: 12,
    retries: 0,
    degraded: false,
  };
}

function renderDashboard(fetchMock = defaultFetchMock()) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  vi.stubGlobal("fetch", fetchMock);

  return render(
    <QueryClientProvider client={queryClient}>
      <MatchDashboard matchId={matchId} />
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

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("deriveScoreline", () => {
  it("uses match stats as the authoritative displayed score", () => {
    expect(deriveScoreline(match, stats)).toEqual({
      home: 3,
      away: 0,
      complete: true,
    });
  });
});

describe("MatchDashboard", () => {
  it("renders match context, stat-sourced score, and timeline events", async () => {
    renderDashboard();

    expect(await screen.findByText("Canada vs Mexico")).toBeInTheDocument();
    expect(await screen.findByText("Score from match stats")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
    expect(screen.getByText("Yellow Card · Mexico")).toBeInTheDocument();
  });

  it("renders an honest empty state when momentum snapshots are missing", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      const body = url.endsWith(`/matches/${matchId}/momentum`)
        ? { momentum: [], meta: meta() }
        : responseFor(url);
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(body),
      });
    });

    renderDashboard(fetchMock);

    expect(await screen.findByText("No momentum snapshots")).toBeInTheDocument();
    expect(screen.getByText("No seeded tactical snapshots are available for this match.")).toBeInTheDocument();
  });

  it("keeps the AI analyst entry point inert until Phase 06", async () => {
    renderDashboard();

    expect(await screen.findByText("AI Analyst")).toBeInTheDocument();
    expect(screen.getByLabelText("Ask AI analyst")).toBeDisabled();
    expect(screen.getByTitle("Available after Phase 06 integration")).toBeInTheDocument();
  });

  it("manually refreshes all dashboard resources", async () => {
    const user = userEvent.setup();
    const fetchMock = defaultFetchMock();
    renderDashboard(fetchMock);

    await screen.findByText("Canada vs Mexico");
    await user.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(8));
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/matches/match-123");
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/matches/match-123/stats");
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/matches/match-123/events");
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/matches/match-123/momentum");
  });
});
