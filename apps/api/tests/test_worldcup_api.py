from fastapi.testclient import TestClient

from app.core.worldcup import MatchCatalogQuery, WorldCupNotFoundError
from app.main import app
from app.routes.worldcup import get_worldcup_catalog


client = TestClient(app)


class FakeWorldCupService:
    async def cities(self) -> list[dict]:
        return [
            {
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            },
            {
                "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                "name": "Vancouver",
                "country_code": "CA",
                "stadium_name": "BC Place",
                "timezone": "America/Vancouver",
            },
        ]

    async def matches(self, query: MatchCatalogQuery) -> dict:
        assert query.city_id is None
        assert query.status is None
        assert query.page == 1
        assert query.page_size == 20
        return {
            "matches": [
                {
                    "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                    "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                    "home_team": "Canada",
                    "away_team": "Mexico",
                    "competition": "FIFA World Cup 2026",
                    "starts_at": "2026-06-12T23:00:00Z",
                    "status": "scheduled",
                    "tags": ["world-cup", "group-stage", "toronto"],
                },
                {
                    "match_id": "cf319c93-5b02-5ec2-9cc5-7194620ee102",
                    "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                    "home_team": "United States",
                    "away_team": "Japan",
                    "competition": "FIFA World Cup 2026",
                    "starts_at": "2026-06-16T02:00:00Z",
                    "status": "scheduled",
                    "tags": ["world-cup", "group-stage", "vancouver"],
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 2,
                "total_pages": 1,
                "has_next": False,
            },
        }

    async def match(self, match_id: str) -> dict:
        assert match_id == "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101"
        return {
            "match": {
                "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                "city": {
                    "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                    "name": "Toronto",
                    "country_code": "CA",
                    "stadium_name": "BMO Field",
                    "timezone": "America/Toronto",
                },
                "home_team": {
                    "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                    "name": "Canada",
                    "country_code": "CA",
                },
                "away_team": {
                    "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                    "name": "Mexico",
                    "country_code": "MX",
                },
                "competition": "FIFA World Cup 2026",
                "stage": "group_stage",
                "starts_at": "2026-06-12T23:00:00Z",
                "status": "scheduled",
                "tags": ["world-cup", "group-stage", "toronto"],
            }
        }

    async def match_stats(self, match_id: str) -> dict:
        assert match_id == "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101"
        return {
            "stats": [
                {
                    "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                    "team_name": "Canada",
                    "goals": 1,
                    "possession_pct": 48.5,
                    "shots": 11,
                    "shots_on_target": 4,
                    "passes": 435,
                    "corners": 5,
                    "fouls": 12,
                },
                {
                    "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                    "team_name": "Mexico",
                    "goals": 1,
                    "possession_pct": 51.5,
                    "shots": 13,
                    "shots_on_target": 5,
                    "passes": 472,
                    "corners": 6,
                    "fouls": 10,
                },
            ]
        }

    async def match_events(self, match_id: str) -> dict:
        assert match_id == "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101"
        return {
            "events": [
                {
                    "event_id": "f4d0ca07-9e1d-5cca-a67d-9564c81b2e01",
                    "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                    "team_name": "Canada",
                    "player_id": "5032f877-60f4-5bf6-b4b4-f948750925f2",
                    "player_name": "Jonathan David",
                    "event_type": "goal",
                    "minute": 24,
                    "stoppage_minute": None,
                    "description": "Canada opens the scoring after a high recovery.",
                },
                {
                    "event_id": "33ae3b27-e43e-5687-a5c8-4bde61fca702",
                    "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                    "team_name": "Mexico",
                    "player_id": "bf1a3b8e-5c81-5f98-a4c9-062d2e7f5401",
                    "player_name": "Santiago Gimenez",
                    "event_type": "goal",
                    "minute": 68,
                    "stoppage_minute": None,
                    "description": "Mexico equalizes from a central combination.",
                },
            ]
        }

    async def match_momentum(self, match_id: str) -> dict:
        assert match_id == "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101"
        return {
            "momentum": [
                {
                    "snapshot_id": "e4bf8c35-f0a2-5036-b88a-098a1d3e0001",
                    "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                    "team_name": "Canada",
                    "minute": 15,
                    "formation": "3-4-2-1",
                    "possession_style": "direct wide progression",
                    "press_intensity": "high",
                    "defensive_line": "mid",
                    "confidence": 0.82,
                },
                {
                    "snapshot_id": "c0f63bd2-adcf-5bff-a3ce-4da3cc620002",
                    "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                    "team_name": "Mexico",
                    "minute": 15,
                    "formation": "4-3-3",
                    "possession_style": "patient central buildup",
                    "press_intensity": "medium",
                    "defensive_line": "high",
                    "confidence": 0.79,
                },
            ]
        }


class MissingMatchWorldCupService(FakeWorldCupService):
    async def match(self, match_id: str) -> dict:
        raise WorldCupNotFoundError(f"World Cup match '{match_id}' was not found.")


def test_list_cities_returns_seeded_host_city_contract() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/cities")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "cities": [
            {
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            },
            {
                "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                "name": "Vancouver",
                "country_code": "CA",
                "stadium_name": "BC Place",
                "timezone": "America/Vancouver",
            },
        ],
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_list_matches_returns_all_cities_by_default() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/matches")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "matches": [
            {
                "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "home_team": "Canada",
                "away_team": "Mexico",
                "competition": "FIFA World Cup 2026",
                "starts_at": "2026-06-12T23:00:00Z",
                    "status": "scheduled",
                    "tags": ["world-cup", "group-stage", "toronto"],
                },
                {
                    "match_id": "cf319c93-5b02-5ec2-9cc5-7194620ee102",
                    "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                    "home_team": "United States",
                    "away_team": "Japan",
                    "competition": "FIFA World Cup 2026",
                    "starts_at": "2026-06-16T02:00:00Z",
                    "status": "scheduled",
                    "tags": ["world-cup", "group-stage", "vancouver"],
                }
            ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total_items": 2,
            "total_pages": 1,
            "has_next": False,
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_match_returns_compact_detail_contract() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/matches/1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "match": {
            "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
            "city": {
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            },
            "home_team": {
                "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                "name": "Canada",
                "country_code": "CA",
            },
            "away_team": {
                "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                "name": "Mexico",
                "country_code": "MX",
            },
            "competition": "FIFA World Cup 2026",
            "stage": "group_stage",
            "starts_at": "2026-06-12T23:00:00Z",
            "status": "scheduled",
            "tags": ["world-cup", "group-stage", "toronto"],
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_match_stats_returns_team_stats_contract() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/matches/1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101/stats")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "stats": [
            {
                "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                "team_name": "Canada",
                "goals": 1,
                "possession_pct": 48.5,
                "shots": 11,
                "shots_on_target": 4,
                "passes": 435,
                "corners": 5,
                "fouls": 12,
            },
            {
                "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                "team_name": "Mexico",
                "goals": 1,
                "possession_pct": 51.5,
                "shots": 13,
                "shots_on_target": 5,
                "passes": 472,
                "corners": 6,
                "fouls": 10,
            },
        ],
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_match_events_returns_timeline_contract() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/matches/1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101/events")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "events": [
            {
                "event_id": "f4d0ca07-9e1d-5cca-a67d-9564c81b2e01",
                "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                "team_name": "Canada",
                "player_id": "5032f877-60f4-5bf6-b4b4-f948750925f2",
                "player_name": "Jonathan David",
                "event_type": "goal",
                "minute": 24,
                "stoppage_minute": None,
                "description": "Canada opens the scoring after a high recovery.",
            },
            {
                "event_id": "33ae3b27-e43e-5687-a5c8-4bde61fca702",
                "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                "team_name": "Mexico",
                "player_id": "bf1a3b8e-5c81-5f98-a4c9-062d2e7f5401",
                "player_name": "Santiago Gimenez",
                "event_type": "goal",
                "minute": 68,
                "stoppage_minute": None,
                "description": "Mexico equalizes from a central combination.",
            },
        ],
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_match_momentum_returns_tactical_snapshots_contract() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: FakeWorldCupService()

    try:
        response = client.get("/matches/1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101/momentum")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "momentum": [
            {
                "snapshot_id": "e4bf8c35-f0a2-5036-b88a-098a1d3e0001",
                "team_id": "968bec99-b07e-5bbf-88c0-37af8fd08da2",
                "team_name": "Canada",
                "minute": 15,
                "formation": "3-4-2-1",
                "possession_style": "direct wide progression",
                "press_intensity": "high",
                "defensive_line": "mid",
                "confidence": 0.82,
            },
            {
                "snapshot_id": "c0f63bd2-adcf-5bff-a3ce-4da3cc620002",
                "team_id": "5baedb39-9cd5-5a02-8b25-9f9c8420c7a5",
                "team_name": "Mexico",
                "minute": 15,
                "formation": "4-3-3",
                "possession_style": "patient central buildup",
                "press_intensity": "medium",
                "defensive_line": "high",
                "confidence": 0.79,
            },
        ],
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_match_returns_structured_not_found_error() -> None:
    app.dependency_overrides[get_worldcup_catalog] = lambda: MissingMatchWorldCupService()

    try:
        response = client.get("/matches/missing-match")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "WORLDCUP_MATCH_NOT_FOUND",
            "message": "World Cup match 'missing-match' was not found.",
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)
