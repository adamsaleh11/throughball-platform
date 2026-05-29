from typing import Optional

from pydantic import BaseModel

from app.models.health import ObservabilityMeta


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool


class City(BaseModel):
    city_id: str
    name: str
    country_code: str
    stadium_name: Optional[str] = None
    timezone: Optional[str] = None


class MatchSummary(BaseModel):
    match_id: str
    city_id: str
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    competition: str
    starts_at: str
    status: str
    tags: list[str]


class TeamSummary(BaseModel):
    team_id: str
    name: str
    country_code: str


class MatchDetail(BaseModel):
    match_id: str
    city: City
    home_team: TeamSummary
    away_team: TeamSummary
    competition: str
    stage: str
    starts_at: str
    status: str
    tags: list[str]


class MatchStats(BaseModel):
    team_id: str
    team_name: str
    goals: int
    possession_pct: Optional[float] = None
    shots: int
    shots_on_target: int
    passes: int
    corners: int
    fouls: int


class MatchEvent(BaseModel):
    event_id: str
    team_id: str
    team_name: str
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    event_type: str
    minute: int
    stoppage_minute: Optional[int] = None
    description: Optional[str] = None


class MatchMomentum(BaseModel):
    snapshot_id: str
    team_id: str
    team_name: str
    minute: int
    formation: str
    possession_style: str
    press_intensity: str
    defensive_line: str
    confidence: float


class CitiesResponse(BaseModel):
    cities: list[City]
    meta: ObservabilityMeta


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]
    pagination: Pagination
    meta: ObservabilityMeta


class MatchDetailResponse(BaseModel):
    match: MatchDetail
    meta: ObservabilityMeta


class MatchStatsResponse(BaseModel):
    stats: list[MatchStats]
    meta: ObservabilityMeta


class MatchEventsResponse(BaseModel):
    events: list[MatchEvent]
    meta: ObservabilityMeta


class MatchMomentumResponse(BaseModel):
    momentum: list[MatchMomentum]
    meta: ObservabilityMeta
