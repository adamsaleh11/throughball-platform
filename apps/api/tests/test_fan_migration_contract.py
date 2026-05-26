from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FAN_MIGRATION = ROOT / "supabase/migrations/202605260002_fan_checkins_hotspots.sql"


def test_fan_migration_creates_required_tables() -> None:
    migration_sql = FAN_MIGRATION.read_text()

    for table in [
        "fan_checkins",
        "fan_rsvps",
        "fan_signals",
        "fan_hotspots",
        "hotspot_history",
    ]:
        assert f"create table if not exists public.{table}" in migration_sql


def test_private_fan_tables_have_user_scoped_rls_policies() -> None:
    migration_sql = FAN_MIGRATION.read_text()

    assert "alter table public.fan_checkins enable row level security" in migration_sql
    assert "with check (user_id = auth.uid() and visibility = 'private')" in migration_sql
    assert "using (user_id = auth.uid())" in migration_sql
    assert "alter table public.fan_rsvps enable row level security" in migration_sql
    assert "alter table public.fan_signals enable row level security" in migration_sql


def test_public_hotspot_tables_are_aggregate_read_only_for_clients() -> None:
    migration_sql = FAN_MIGRATION.read_text()

    assert "alter table public.fan_hotspots enable row level security" in migration_sql
    assert "create policy \"fan hotspots are publicly readable\"" in migration_sql
    assert "create policy \"hotspot history is publicly readable\"" in migration_sql
    assert "source in ('seeded', 'manual') or supporter_count >= 3" in migration_sql
    assert "for insert\non public.fan_hotspots" not in migration_sql
    assert "for update\non public.fan_hotspots" not in migration_sql
