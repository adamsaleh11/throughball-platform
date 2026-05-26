import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_DATA = ROOT / "apps/web/lib/reference-data.ts"
AUTH_PROFILE_MIGRATION = ROOT / "supabase/migrations/202605250202_supabase_auth_profile.sql"
WORLDCUP_MIGRATION = ROOT / "supabase/migrations/202605260001_worldcup_core_schema.sql"
EXPANDED_TAGS_MIGRATION = (
    ROOT / "supabase/migrations/202605260001_expand_preferred_match_tags.sql"
)


def _array_body(source: str, export_name: str) -> str:
    pattern = rf"export const {export_name} = \[(.*?)\];"
    match = re.search(pattern, source, re.DOTALL)
    assert match is not None, f"{export_name} was not found in frontend reference data."
    return match.group(1)


def _frontend_ids(export_name: str) -> set[str]:
    source = REFERENCE_DATA.read_text()
    body = _array_body(source, export_name)
    return set(re.findall(r'id: "([^"]+)"', body))


def _seeded_ids(table_name: str) -> set[str]:
    migration_sql = AUTH_PROFILE_MIGRATION.read_text() + "\n" + WORLDCUP_MIGRATION.read_text()
    table_sql = "\n".join(
        block
        for block in migration_sql.split("insert into public.")
        if block.startswith(f"{table_name} ")
    )
    return set(re.findall(r"\('([0-9a-f-]{36})'", table_sql))


def test_frontend_host_city_ids_are_seeded_by_supabase_migrations() -> None:
    assert _frontend_ids("hostCities") <= _seeded_ids("host_cities")


def test_frontend_team_ids_are_seeded_by_supabase_migrations() -> None:
    assert _frontend_ids("teams") <= _seeded_ids("teams")


def test_frontend_uses_latest_seeded_host_city_label() -> None:
    source = REFERENCE_DATA.read_text()

    assert "New York/New Jersey" in source
    assert "New York/NJ" not in source


def test_expanded_frontend_experience_tags_are_not_blocked_by_legacy_allowlist() -> None:
    migration_sql = EXPANDED_TAGS_MIGRATION.read_text()

    assert "drop constraint if exists preferred_match_tags_allowed" in migration_sql
