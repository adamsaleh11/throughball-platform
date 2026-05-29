#!/usr/bin/env python3
import argparse
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests


API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
PROVIDER_NAMESPACE = uuid.UUID("95c61985-6007-4b97-8c4f-77238f553f42")

HOST_CITY_IDS = {
    "toronto": "874c6b46-de32-5014-8e54-da12587a7d7f",
    "vancouver": "474d6beb-b593-5c05-92c4-a06aa502dbed",
    "guadalajara": "b671a503-b59c-5d9f-a123-9b1ea8a2c0d6",
    "mexico city": "b3a9b5e9-741b-591c-835c-a6f0d06e0f91",
    "monterrey": "22a9693c-c752-5a4d-bacc-d2d30e7184b3",
    "atlanta": "c50bfe5b-7584-5cbc-986a-3181ad4e24a5",
    "boston": "de87922f-8512-5575-90ee-38d8c10282fe",
    "dallas": "b865e6bf-eb90-593f-aa76-7ffb55fd9fda",
    "houston": "713d1905-0f40-57b5-84fc-4409f300c919",
    "kansas city": "4da740f5-55c8-53a1-bc01-2f16e943110d",
    "los angeles": "8b2dc317-8b49-5b8a-8544-7d091044b4e1",
    "miami": "bd337c08-d7f9-57bb-8a33-c2feeb3ca18f",
    "new york/new jersey": "e0452c84-d22b-54b2-9f48-6805f73801c6",
    "philadelphia": "4d1935bc-b2b5-5ebf-9ea9-36ba368d8972",
    "san francisco bay area": "cc33e2c4-6c1c-5d5b-8985-6015ed027a07",
    "seattle": "e5fae842-3ec7-5636-a2ae-ebb90793ee85",
}

COUNTRY_CODE_OVERRIDES = {
    "CAN": "CA",
    "MEX": "MX",
    "USA": "US",
}

STATUS_MAP = {
    "NS": "scheduled",
    "TBD": "scheduled",
    "1H": "live",
    "HT": "live",
    "2H": "live",
    "ET": "live",
    "P": "live",
    "FT": "completed",
    "AET": "completed",
    "PEN": "completed",
    "PST": "postponed",
    "CANC": "cancelled",
}


@dataclass(frozen=True)
class ImportedTeam:
    team_id: str
    provider_id: int
    name: str
    country_code: str


@dataclass(frozen=True)
class ImportedMatch:
    match_id: str
    provider_id: int
    city_id: str
    home_team_id: str
    away_team_id: str
    competition: str
    stage: str
    kickoff_time: str
    status: str
    tags: list[str]


@dataclass(frozen=True)
class ImportSeed:
    teams: list[ImportedTeam]
    matches: list[ImportedMatch]
    skipped: list[str]


def provider_uuid(kind: str, provider_id: int) -> str:
    return str(uuid.uuid5(PROVIDER_NAMESPACE, f"api-football:{kind}:{provider_id}"))


def normalize_fixtures(payload: dict[str, Any]) -> ImportSeed:
    teams_by_id: dict[int, ImportedTeam] = {}
    matches: list[ImportedMatch] = []
    skipped: list[str] = []

    for item in payload.get("response", []):
        fixture = item.get("fixture", {})
        fixture_id = fixture.get("id")
        venue = fixture.get("venue") or {}
        city_id = city_id_for_venue(venue)
        if not fixture_id or not city_id:
            skipped.append(f"fixture:{fixture_id or 'unknown'} missing supported host city")
            continue

        home = normalize_team(item.get("teams", {}).get("home", {}))
        away = normalize_team(item.get("teams", {}).get("away", {}))
        if not home or not away:
            skipped.append(f"fixture:{fixture_id} missing teams")
            continue

        teams_by_id[home.provider_id] = home
        teams_by_id[away.provider_id] = away
        league = item.get("league", {})
        status_short = (fixture.get("status") or {}).get("short")
        round_name = league.get("round") or "unknown"
        tags = ["world-cup", slugify(round_name), slugify(venue.get("city") or "host-city")]
        matches.append(
            ImportedMatch(
                match_id=provider_uuid("fixture", int(fixture_id)),
                provider_id=int(fixture_id),
                city_id=city_id,
                home_team_id=home.team_id,
                away_team_id=away.team_id,
                competition=league.get("name") or "FIFA World Cup 2026",
                stage=slugify(round_name).replace("-", "_"),
                kickoff_time=normalize_datetime(fixture.get("date")),
                status=STATUS_MAP.get(status_short, "scheduled"),
                tags=tags,
            )
        )

    return ImportSeed(
        teams=sorted(teams_by_id.values(), key=lambda team: team.name),
        matches=sorted(matches, key=lambda match: match.kickoff_time),
        skipped=skipped,
    )


def normalize_team(raw: dict[str, Any]) -> Optional[ImportedTeam]:
    provider_id = raw.get("id")
    name = raw.get("name")
    if not provider_id or not name:
        return None
    code = raw.get("code") or raw.get("country") or "UN"
    return ImportedTeam(
        team_id=provider_uuid("team", int(provider_id)),
        provider_id=int(provider_id),
        name=name,
        country_code=COUNTRY_CODE_OVERRIDES.get(code, code[:2].upper()),
    )


def city_id_for_venue(venue: dict[str, Any]) -> Optional[str]:
    city = normalize_city_name(venue.get("city") or "")
    if city in HOST_CITY_IDS:
        return HOST_CITY_IDS[city]
    name = normalize_city_name(venue.get("name") or "")
    for known_city, city_id in HOST_CITY_IDS.items():
        if known_city in name:
            return city_id
    return None


def normalize_city_name(value: str) -> str:
    return " ".join(value.lower().replace(",", " ").split())


def normalize_datetime(value: Optional[str]) -> str:
    if not value:
        raise ValueError("fixture date is required")
    return value.replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in slug.split("-") if part)


def render_seed_sql(seed: ImportSeed) -> str:
    lines = [
        "-- Generated by scripts/import_api_football_worldcup.py.",
        "-- Provider-derived data: keep local unless licensing permits committing.",
        "",
    ]
    if seed.teams:
        lines.extend(render_teams_sql(seed.teams))
        lines.append("")
    if seed.matches:
        lines.extend(render_matches_sql(seed.matches))
        lines.append("")
    if seed.skipped:
        lines.append("-- Skipped fixtures:")
        lines.extend(f"-- {reason}" for reason in seed.skipped)
        lines.append("")
    return "\n".join(lines)


def render_teams_sql(teams: list[ImportedTeam]) -> list[str]:
    values = [
        f"  ({sql_string(team.team_id)}, {sql_string(team.name)}, {sql_string(team.country_code)})"
        for team in teams
    ]
    return [
        "insert into public.teams (id, name, country_code)",
        "values",
        ",\n".join(values),
        "on conflict (id) do update set",
        "  name = excluded.name,",
        "  country_code = excluded.country_code;",
    ]


def render_matches_sql(matches: list[ImportedMatch]) -> list[str]:
    values = [
        "  ("
        + ", ".join(
            [
                sql_string(match.match_id),
                sql_string(match.city_id),
                sql_string(match.home_team_id),
                sql_string(match.away_team_id),
                sql_string(match.competition),
                sql_string(match.stage),
                sql_string(match.kickoff_time),
                sql_string(match.status),
                sql_text_array(match.tags),
            ]
        )
        + ")"
        for match in matches
    ]
    return [
        "insert into public.matches (",
        "  id, city_id, home_team_id, away_team_id, competition, stage, kickoff_time, status, tags",
        ")",
        "values",
        ",\n".join(values),
        "on conflict (id) do update set",
        "  city_id = excluded.city_id,",
        "  home_team_id = excluded.home_team_id,",
        "  away_team_id = excluded.away_team_id,",
        "  competition = excluded.competition,",
        "  stage = excluded.stage,",
        "  kickoff_time = excluded.kickoff_time,",
        "  status = excluded.status,",
        "  tags = excluded.tags;",
    ]


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_text_array(values: list[str]) -> str:
    return "array[" + ", ".join(sql_string(value) for value in values) + "]::text[]"


def fetch_fixtures(api_key: str, league_id: int, season: int) -> dict[str, Any]:
    response = requests.get(
        f"{API_FOOTBALL_BASE_URL}/fixtures",
        headers={"x-apisports-key": api_key},
        params={"league": league_id, "season": season},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    errors = payload.get("errors")
    if errors:
        raise RuntimeError(f"API-Football returned errors: {errors}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch API-Football World Cup fixtures and emit local Supabase seed SQL."
    )
    parser.add_argument("--league-id", type=int, default=WORLD_CUP_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=WORLD_CUP_SEASON)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("supabase/generated/api-football-worldcup.sql"),
    )
    parser.add_argument("--input-json", type=Path, help="Read an existing provider JSON file.")
    args = parser.parse_args()

    if args.input_json:
        payload = json.loads(args.input_json.read_text())
    else:
        api_key = os.environ.get("API_FOOTBALL_KEY")
        if not api_key:
            raise SystemExit("API_FOOTBALL_KEY is required unless --input-json is used.")
        payload = fetch_fixtures(api_key, args.league_id, args.season)

    seed = normalize_fixtures(payload)
    sql = render_seed_sql(seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sql)
    print(
        f"wrote {args.output} with {len(seed.teams)} teams, "
        f"{len(seed.matches)} matches, {len(seed.skipped)} skipped fixtures"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
