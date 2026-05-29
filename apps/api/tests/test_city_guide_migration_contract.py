from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202605280001_host_city_intelligence.sql"

HOST_CITY_IDS = [
    "874c6b46-de32-5014-8e54-da12587a7d7f",
    "474d6beb-b593-5c05-92c4-a06aa502dbed",
    "b671a503-b59c-5d9f-a123-9b1ea8a2c0d6",
    "b3a9b5e9-741b-591c-835c-a6f0d06e0f91",
    "22a9693c-c752-5a4d-bacc-d2d30e7184b3",
    "c50bfe5b-7584-5cbc-986a-3181ad4e24a5",
    "de87922f-8512-5575-90ee-38d8c10282fe",
    "b865e6bf-eb90-593f-aa76-7ffb55fd9fda",
    "713d1905-0f40-57b5-84fc-4409f300c919",
    "4da740f5-55c8-53a1-bc01-2f16e943110d",
    "8b2dc317-8b49-5b8a-8544-7d091044b4e1",
    "bd337c08-d7f9-57bb-8a33-c2feeb3ca18f",
    "e0452c84-d22b-54b2-9f48-6805f73801c6",
    "4d1935bc-b2b5-5ebf-9ea9-36ba368d8972",
    "cc33e2c4-6c1c-5d5b-8985-6015ed027a07",
    "e5fae842-3ec7-5636-a2ae-ebb90793ee85",
]


def migration_sql() -> str:
    return MIGRATION.read_text()


def test_city_guide_migration_creates_required_tables() -> None:
    sql = migration_sql()

    for table in ["venues", "city_events", "tourist_spots", "transport_hubs"]:
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"on public.{table}\nfor select\nusing (true)" in sql


def test_city_guide_tables_reference_host_cities_and_keep_sources() -> None:
    sql = migration_sql()

    assert "city_id uuid not null references public.host_cities(id)" in sql
    for field in ["source_name text not null", "source_url text not null", "data_origin text not null", "last_verified_at date not null"]:
        assert sql.count(field) >= 4


def test_city_guide_seed_data_covers_all_existing_host_cities() -> None:
    sql = migration_sql()

    for city_id in HOST_CITY_IDS:
        assert city_id in sql

    assert "FIFA World Cup 26" in sql
    assert "Wikidata" in sql
    assert "dummy" not in sql.lower()
