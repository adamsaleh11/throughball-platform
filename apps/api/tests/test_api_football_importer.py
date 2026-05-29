from scripts.import_api_football_worldcup import normalize_fixtures, render_seed_sql


def test_importer_normalizes_worldcup_fixture_without_provider_key() -> None:
    payload = {
        "response": [
            {
                "fixture": {
                    "id": 12345,
                    "date": "2026-06-12T23:00:00+00:00",
                    "status": {"short": "NS"},
                    "venue": {"city": "Toronto", "name": "BMO Field"},
                },
                "league": {"name": "FIFA World Cup", "round": "Group Stage"},
                "teams": {
                    "home": {"id": 5529, "name": "Canada", "code": "CAN"},
                    "away": {"id": 16, "name": "Mexico", "code": "MEX"},
                },
            }
        ]
    }

    seed = normalize_fixtures(payload)

    assert seed.skipped == []
    assert [team.name for team in seed.teams] == ["Canada", "Mexico"]
    assert seed.matches[0].city_id == "874c6b46-de32-5014-8e54-da12587a7d7f"
    assert seed.matches[0].home_team_id == seed.teams[0].team_id
    assert seed.matches[0].away_team_id == seed.teams[1].team_id
    assert seed.matches[0].status == "scheduled"


def test_importer_rendered_sql_is_idempotent_and_does_not_include_secrets() -> None:
    payload = {
        "response": [
            {
                "fixture": {
                    "id": 12345,
                    "date": "2026-06-12T23:00:00+00:00",
                    "status": {"short": "NS"},
                    "venue": {"city": "Toronto", "name": "BMO Field"},
                },
                "league": {"name": "FIFA World Cup", "round": "Group Stage"},
                "teams": {
                    "home": {"id": 5529, "name": "Canada", "code": "CAN"},
                    "away": {"id": 16, "name": "Mexico", "code": "MEX"},
                },
            }
        ]
    }

    sql = render_seed_sql(normalize_fixtures(payload))

    assert "insert into public.teams" in sql
    assert "insert into public.matches" in sql
    assert "on conflict (id) do update" in sql
    assert "API_FOOTBALL_KEY" not in sql
    assert "test_provider_secret_value" not in sql
