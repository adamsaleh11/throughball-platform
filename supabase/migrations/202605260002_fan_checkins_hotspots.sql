create extension if not exists pgcrypto;

create table if not exists public.fan_checkins (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  city_id uuid not null references public.host_cities(id) on delete restrict,
  match_id uuid null references public.matches(id) on delete set null,
  venue_id uuid null,
  latitude numeric(9,6) not null check (latitude between -90 and 90),
  longitude numeric(9,6) not null check (longitude between -180 and 180),
  visibility text not null default 'private',
  checked_in_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  constraint fan_checkins_visibility_allowed check (visibility in ('private'))
);

create table if not exists public.fan_rsvps (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  city_id uuid not null references public.host_cities(id) on delete restrict,
  match_id uuid null references public.matches(id) on delete cascade,
  venue_id uuid null,
  status text not null default 'interested',
  party_size integer not null default 1 check (party_size between 1 and 20),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fan_rsvps_status_allowed check (status in ('interested', 'going', 'cancelled'))
);

create table if not exists public.fan_signals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null references public.profiles(id) on delete cascade,
  city_id uuid not null references public.host_cities(id) on delete restrict,
  match_id uuid null references public.matches(id) on delete cascade,
  venue_id uuid null,
  signal_type text not null,
  signal_weight numeric(5,3) not null default 1 check (signal_weight between 0 and 10),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint fan_signals_type_allowed check (
    signal_type in ('checkin', 'rsvp', 'venue_interest', 'manual_seed')
  )
);

create table if not exists public.fan_hotspots (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete cascade,
  match_id uuid null references public.matches(id) on delete cascade,
  area_label text not null,
  center_lat numeric(9,6) not null check (center_lat between -90 and 90),
  center_lng numeric(9,6) not null check (center_lng between -180 and 180),
  center_precision text not null default 'neighborhood',
  score integer not null check (score between 0 and 100),
  confidence numeric(4,3) not null check (confidence between 0 and 1),
  supporter_count integer not null check (supporter_count >= 0),
  top_venue_ids uuid[] not null default '{}',
  ranking_factors jsonb not null default '{}'::jsonb,
  source text not null default 'seeded',
  updated_at timestamptz not null default now(),
  constraint fan_hotspots_center_precision_allowed check (
    center_precision in ('city', 'neighborhood', 'area')
  ),
  constraint fan_hotspots_source_allowed check (source in ('seeded', 'manual', 'aggregate')),
  constraint fan_hotspots_public_minimum check (
    source in ('seeded', 'manual') or supporter_count >= 3
  )
);

create table if not exists public.hotspot_history (
  id uuid primary key default gen_random_uuid(),
  hotspot_id uuid not null references public.fan_hotspots(id) on delete cascade,
  city_id uuid not null references public.host_cities(id) on delete cascade,
  match_id uuid null references public.matches(id) on delete cascade,
  score integer not null check (score between 0 and 100),
  confidence numeric(4,3) not null check (confidence between 0 and 1),
  supporter_count integer not null check (supporter_count >= 0),
  ranking_factors jsonb not null default '{}'::jsonb,
  recorded_at timestamptz not null default now()
);

create index if not exists idx_fan_checkins_user_id_checked_in_at
  on public.fan_checkins(user_id, checked_in_at desc);

create index if not exists idx_fan_checkins_city_id_checked_in_at
  on public.fan_checkins(city_id, checked_in_at desc);

create index if not exists idx_fan_checkins_match_id
  on public.fan_checkins(match_id);

create index if not exists idx_fan_rsvps_user_id
  on public.fan_rsvps(user_id);

create index if not exists idx_fan_rsvps_city_id
  on public.fan_rsvps(city_id);

create index if not exists idx_fan_signals_city_id_created_at
  on public.fan_signals(city_id, created_at desc);

create index if not exists idx_fan_hotspots_city_id_score
  on public.fan_hotspots(city_id, score desc);

create index if not exists idx_fan_hotspots_match_id
  on public.fan_hotspots(match_id);

create index if not exists idx_hotspot_history_hotspot_id_recorded_at
  on public.hotspot_history(hotspot_id, recorded_at desc);

drop trigger if exists set_fan_rsvps_updated_at on public.fan_rsvps;
create trigger set_fan_rsvps_updated_at
before update on public.fan_rsvps
for each row execute function public.set_updated_at();

alter table public.fan_checkins enable row level security;
alter table public.fan_rsvps enable row level security;
alter table public.fan_signals enable row level security;
alter table public.fan_hotspots enable row level security;
alter table public.hotspot_history enable row level security;

drop policy if exists "users can read own fan checkins" on public.fan_checkins;
create policy "users can read own fan checkins"
on public.fan_checkins
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own fan checkins" on public.fan_checkins;
create policy "users can insert own fan checkins"
on public.fan_checkins
for insert
to authenticated
with check (user_id = auth.uid() and visibility = 'private');

drop policy if exists "users can read own fan rsvps" on public.fan_rsvps;
create policy "users can read own fan rsvps"
on public.fan_rsvps
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own fan rsvps" on public.fan_rsvps;
create policy "users can insert own fan rsvps"
on public.fan_rsvps
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "users can update own fan rsvps" on public.fan_rsvps;
create policy "users can update own fan rsvps"
on public.fan_rsvps
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "users can delete own fan rsvps" on public.fan_rsvps;
create policy "users can delete own fan rsvps"
on public.fan_rsvps
for delete
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can read own fan signals" on public.fan_signals;
create policy "users can read own fan signals"
on public.fan_signals
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own fan signals" on public.fan_signals;
create policy "users can insert own fan signals"
on public.fan_signals
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "fan hotspots are publicly readable" on public.fan_hotspots;
create policy "fan hotspots are publicly readable"
on public.fan_hotspots
for select
using (true);

drop policy if exists "hotspot history is publicly readable" on public.hotspot_history;
create policy "hotspot history is publicly readable"
on public.hotspot_history
for select
using (true);

insert into public.fan_hotspots (
  id,
  city_id,
  match_id,
  area_label,
  center_lat,
  center_lng,
  center_precision,
  score,
  confidence,
  supporter_count,
  top_venue_ids,
  ranking_factors,
  source,
  updated_at
)
values
  (
    '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d001',
    '874c6b46-de32-5014-8e54-da12587a7d7f',
    '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101',
    'Queen West',
    43.642600,
    -79.416300,
    'neighborhood',
    91,
    0.860,
    240,
    array['11111111-1111-1111-1111-111111111101']::uuid[],
    '{"check_in_weight": 0.45, "rsvp_weight": 0.25, "signal_weight": 0.20, "recency_weight": 0.10}'::jsonb,
    'seeded',
    '2026-05-26T12:10:00Z'
  ),
  (
    '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d002',
    '474d6beb-b593-5c05-92c4-a06aa502dbed',
    'cf319c93-5b02-5ec2-9cc5-7194620ee102',
    'Downtown Vancouver',
    49.282700,
    -123.120700,
    'neighborhood',
    88,
    0.830,
    190,
    array['11111111-1111-1111-1111-111111111102']::uuid[],
    '{"check_in_weight": 0.42, "rsvp_weight": 0.28, "signal_weight": 0.20, "recency_weight": 0.10}'::jsonb,
    'seeded',
    '2026-05-26T12:10:00Z'
  ),
  (
    '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d003',
    'bd337c08-d7f9-57bb-8a33-c2feeb3ca18f',
    null,
    'Wynwood',
    25.801000,
    -80.199000,
    'neighborhood',
    84,
    0.780,
    160,
    array['11111111-1111-1111-1111-111111111103']::uuid[],
    '{"check_in_weight": 0.40, "rsvp_weight": 0.25, "signal_weight": 0.25, "recency_weight": 0.10}'::jsonb,
    'seeded',
    '2026-05-26T12:10:00Z'
  )
on conflict (id) do update set
  city_id = excluded.city_id,
  match_id = excluded.match_id,
  area_label = excluded.area_label,
  center_lat = excluded.center_lat,
  center_lng = excluded.center_lng,
  center_precision = excluded.center_precision,
  score = excluded.score,
  confidence = excluded.confidence,
  supporter_count = excluded.supporter_count,
  top_venue_ids = excluded.top_venue_ids,
  ranking_factors = excluded.ranking_factors,
  source = excluded.source,
  updated_at = excluded.updated_at;

insert into public.hotspot_history (
  hotspot_id,
  city_id,
  match_id,
  score,
  confidence,
  supporter_count,
  ranking_factors,
  recorded_at
)
select
  id,
  city_id,
  match_id,
  score,
  confidence,
  supporter_count,
  ranking_factors,
  updated_at
from public.fan_hotspots
where id in (
  '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d001',
  '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d002',
  '8a31f6b5-a1a6-5df8-9f3d-c53b7c43d003'
);
