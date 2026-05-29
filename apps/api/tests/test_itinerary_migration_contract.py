from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202605280002_itinerary_persistence.sql"


def migration_sql() -> str:
    return MIGRATION.read_text()


def test_itinerary_migration_creates_required_tables() -> None:
    sql = migration_sql()

    for table in ["itineraries", "itinerary_items"]:
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql


def test_itinerary_tables_are_user_scoped_and_deduplicated_by_input_hash() -> None:
    sql = migration_sql()

    assert "user_id uuid not null references public.profiles(id) on delete cascade" in sql
    assert "unique (user_id, input_hash)" in sql
    assert "itinerary_id uuid not null references public.itineraries(id) on delete cascade" in sql
    assert "unique (itinerary_id, position)" in sql


def test_itinerary_rls_policies_do_not_grant_public_access() -> None:
    sql = migration_sql()

    assert "using (user_id = auth.uid())" in sql
    assert "with check (user_id = auth.uid())" in sql
    assert "auth.uid() = (select user_id from public.itineraries where id = itinerary_id)" in sql
    assert "using (true)" not in sql
    assert "to anon" not in sql
