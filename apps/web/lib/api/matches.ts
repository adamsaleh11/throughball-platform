const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ObservabilityMeta = {
  request_id: string;
  trace_id: string;
  latency_ms: number;
  retries: number;
  degraded: boolean;
};

export type TeamSummary = {
  team_id: string;
  name: string;
  country_code: string;
};

export type MatchDetail = {
  match_id: string;
  city: {
    city_id: string;
    name: string;
    country_code: string;
    stadium_name?: string | null;
    timezone?: string | null;
  };
  home_team: TeamSummary;
  away_team: TeamSummary;
  competition: string;
  stage: string;
  starts_at: string;
  status: string;
  tags: string[];
};

export type MatchStat = {
  team_id: string;
  team_name: string;
  goals: number;
  possession_pct: number | null;
  shots: number;
  shots_on_target: number;
  passes: number;
  corners: number;
  fouls: number;
};

export type MatchEvent = {
  event_id: string;
  team_id: string;
  team_name: string;
  player_id: string | null;
  player_name: string | null;
  event_type: string;
  minute: number;
  stoppage_minute: number | null;
  description: string | null;
};

export type MatchMomentum = {
  snapshot_id: string;
  team_id: string;
  team_name: string;
  minute: number;
  formation: string;
  possession_style: string;
  press_intensity: string;
  defensive_line: string;
  confidence: number;
};

export type MatchDetailResponse = {
  match: MatchDetail;
  meta: ObservabilityMeta;
};

export type MatchStatsResponse = {
  stats: MatchStat[];
  meta: ObservabilityMeta;
};

export type MatchEventsResponse = {
  events: MatchEvent[];
  meta: ObservabilityMeta;
};

export type MatchMomentumResponse = {
  momentum: MatchMomentum[];
  meta: ObservabilityMeta;
};

async function getJson<TResponse>(path: string, errorMessage: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new Error(errorMessage);
  return response.json();
}

export function fetchMatch(matchId: string): Promise<MatchDetailResponse> {
  return getJson(`/matches/${matchId}`, "Unable to load match.");
}

export function fetchMatchStats(matchId: string): Promise<MatchStatsResponse> {
  return getJson(`/matches/${matchId}/stats`, "Unable to load match stats.");
}

export function fetchMatchEvents(matchId: string): Promise<MatchEventsResponse> {
  return getJson(`/matches/${matchId}/events`, "Unable to load match events.");
}

export function fetchMatchMomentum(matchId: string): Promise<MatchMomentumResponse> {
  return getJson(`/matches/${matchId}/momentum`, "Unable to load match momentum.");
}
