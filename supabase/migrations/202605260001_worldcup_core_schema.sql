create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

alter table public.host_cities
add column if not exists timezone text null;

alter table public.host_cities
add column if not exists updated_at timestamptz not null default now();

alter table public.teams
add column if not exists group_code text null;

alter table public.teams
add column if not exists fifa_ranking integer null check (fifa_ranking is null or fifa_ranking > 0);

alter table public.teams
add column if not exists updated_at timestamptz not null default now();

create table if not exists public.players (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null references public.teams(id) on delete cascade,
  full_name text not null,
  position text not null,
  shirt_number integer null check (shirt_number is null or shirt_number between 1 and 99),
  created_at timestamptz not null default now()
);

create table if not exists public.matches (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete restrict,
  home_team_id uuid not null references public.teams(id) on delete restrict,
  away_team_id uuid not null references public.teams(id) on delete restrict,
  competition text not null,
  stage text not null,
  kickoff_time timestamptz not null,
  status text not null default 'scheduled',
  tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint matches_distinct_teams check (home_team_id <> away_team_id),
  constraint matches_status_allowed check (
    status in ('scheduled', 'live', 'completed', 'postponed', 'cancelled')
  )
);

create table if not exists public.match_stats (
  match_id uuid not null references public.matches(id) on delete cascade,
  team_id uuid not null references public.teams(id) on delete cascade,
  goals integer not null default 0 check (goals >= 0),
  possession_pct numeric(5,2) null check (possession_pct is null or possession_pct between 0 and 100),
  shots integer not null default 0 check (shots >= 0),
  shots_on_target integer not null default 0 check (shots_on_target >= 0),
  passes integer not null default 0 check (passes >= 0),
  corners integer not null default 0 check (corners >= 0),
  fouls integer not null default 0 check (fouls >= 0),
  updated_at timestamptz not null default now(),
  primary key (match_id, team_id)
);

create table if not exists public.match_events (
  id uuid primary key default gen_random_uuid(),
  match_id uuid not null references public.matches(id) on delete cascade,
  team_id uuid not null references public.teams(id) on delete cascade,
  player_id uuid null references public.players(id) on delete set null,
  event_type text not null,
  minute integer not null check (minute between 0 and 130),
  stoppage_minute integer null check (stoppage_minute is null or stoppage_minute between 1 and 30),
  description text null,
  created_at timestamptz not null default now(),
  constraint match_events_type_allowed check (
    event_type in ('goal', 'yellow_card', 'red_card', 'substitution', 'var_review')
  )
);

create table if not exists public.tactical_snapshots (
  id uuid primary key default gen_random_uuid(),
  match_id uuid not null references public.matches(id) on delete cascade,
  team_id uuid not null references public.teams(id) on delete cascade,
  snapshot_minute integer not null check (snapshot_minute between 0 and 130),
  formation text not null,
  possession_style text not null,
  press_intensity text not null,
  defensive_line text not null,
  confidence numeric(4,3) not null check (confidence between 0 and 1),
  created_at timestamptz not null default now(),
  unique (match_id, team_id, snapshot_minute)
);

create index if not exists idx_players_team_id
  on public.players(team_id);

create index if not exists idx_matches_city_id
  on public.matches(city_id);

create index if not exists idx_matches_home_team_id
  on public.matches(home_team_id);

create index if not exists idx_matches_away_team_id
  on public.matches(away_team_id);

create index if not exists idx_matches_kickoff_time
  on public.matches(kickoff_time);

create index if not exists idx_matches_city_id_kickoff_time
  on public.matches(city_id, kickoff_time);

create index if not exists idx_match_stats_match_id
  on public.match_stats(match_id);

create index if not exists idx_match_stats_team_id
  on public.match_stats(team_id);

create index if not exists idx_match_events_match_id
  on public.match_events(match_id);

create index if not exists idx_match_events_team_id
  on public.match_events(team_id);

create index if not exists idx_match_events_match_id_minute
  on public.match_events(match_id, minute);

create index if not exists idx_tactical_snapshots_match_id
  on public.tactical_snapshots(match_id);

create index if not exists idx_tactical_snapshots_team_id
  on public.tactical_snapshots(team_id);

drop trigger if exists set_host_cities_updated_at on public.host_cities;
create trigger set_host_cities_updated_at
before update on public.host_cities
for each row execute function public.set_updated_at();

drop trigger if exists set_teams_updated_at on public.teams;
create trigger set_teams_updated_at
before update on public.teams
for each row execute function public.set_updated_at();

drop trigger if exists set_matches_updated_at on public.matches;
create trigger set_matches_updated_at
before update on public.matches
for each row execute function public.set_updated_at();

alter table public.players enable row level security;
alter table public.matches enable row level security;
alter table public.match_stats enable row level security;
alter table public.match_events enable row level security;
alter table public.tactical_snapshots enable row level security;

drop policy if exists "players are publicly readable" on public.players;
create policy "players are publicly readable"
on public.players
for select
using (true);

drop policy if exists "matches are publicly readable" on public.matches;
create policy "matches are publicly readable"
on public.matches
for select
using (true);

drop policy if exists "match stats are publicly readable" on public.match_stats;
create policy "match stats are publicly readable"
on public.match_stats
for select
using (true);

drop policy if exists "match events are publicly readable" on public.match_events;
create policy "match events are publicly readable"
on public.match_events
for select
using (true);

drop policy if exists "tactical snapshots are publicly readable" on public.tactical_snapshots;
create policy "tactical snapshots are publicly readable"
on public.tactical_snapshots
for select
using (true);

insert into public.host_cities (id, name, country_code, stadium_name, timezone)
values
  ('874c6b46-de32-5014-8e54-da12587a7d7f', 'Toronto', 'CA', 'BMO Field', 'America/Toronto'),
  ('474d6beb-b593-5c05-92c4-a06aa502dbed', 'Vancouver', 'CA', 'BC Place', 'America/Vancouver'),
  ('b671a503-b59c-5d9f-a123-9b1ea8a2c0d6', 'Guadalajara', 'MX', 'Estadio Akron', 'America/Mexico_City'),
  ('b3a9b5e9-741b-591c-835c-a6f0d06e0f91', 'Mexico City', 'MX', 'Estadio Azteca', 'America/Mexico_City'),
  ('22a9693c-c752-5a4d-bacc-d2d30e7184b3', 'Monterrey', 'MX', 'Estadio BBVA', 'America/Monterrey'),
  ('c50bfe5b-7584-5cbc-986a-3181ad4e24a5', 'Atlanta', 'US', 'Mercedes-Benz Stadium', 'America/New_York'),
  ('de87922f-8512-5575-90ee-38d8c10282fe', 'Boston', 'US', 'Gillette Stadium', 'America/New_York'),
  ('b865e6bf-eb90-593f-aa76-7ffb55fd9fda', 'Dallas', 'US', 'AT&T Stadium', 'America/Chicago'),
  ('713d1905-0f40-57b5-84fc-4409f300c919', 'Houston', 'US', 'NRG Stadium', 'America/Chicago'),
  ('4da740f5-55c8-53a1-bc01-2f16e943110d', 'Kansas City', 'US', 'GEHA Field at Arrowhead Stadium', 'America/Chicago'),
  ('8b2dc317-8b49-5b8a-8544-7d091044b4e1', 'Los Angeles', 'US', 'SoFi Stadium', 'America/Los_Angeles'),
  ('bd337c08-d7f9-57bb-8a33-c2feeb3ca18f', 'Miami', 'US', 'Hard Rock Stadium', 'America/New_York'),
  ('e0452c84-d22b-54b2-9f48-6805f73801c6', 'New York/New Jersey', 'US', 'MetLife Stadium', 'America/New_York'),
  ('4d1935bc-b2b5-5ebf-9ea9-36ba368d8972', 'Philadelphia', 'US', 'Lincoln Financial Field', 'America/New_York'),
  ('cc33e2c4-6c1c-5d5b-8985-6015ed027a07', 'San Francisco Bay Area', 'US', 'Levi''s Stadium', 'America/Los_Angeles'),
  ('e5fae842-3ec7-5636-a2ae-ebb90793ee85', 'Seattle', 'US', 'Lumen Field', 'America/Los_Angeles')
on conflict (id) do update set
  name = excluded.name,
  country_code = excluded.country_code,
  stadium_name = excluded.stadium_name,
  timezone = excluded.timezone;

insert into public.teams (id, name, country_code)
values
  ('968bec99-b07e-5bbf-88c0-37af8fd08da2', 'Canada', 'CA'),
  ('5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 'Mexico', 'MX'),
  ('21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 'United States', 'US'),
  ('91a1a6ae-6a33-50bd-855f-e6f054ccfdab', 'Australia', 'AU'),
  ('21415ca8-4840-5a23-b60c-db3a88f2f7c1', 'IR Iran', 'IR'),
  ('6e45bc34-588b-5fa6-bc54-31076a776b82', 'Iraq', 'IQ'),
  ('3b596604-101b-5078-b81f-a0a2d331067b', 'Japan', 'JP'),
  ('e67134d3-0ffa-5bad-be66-15a7760fedda', 'Jordan', 'JO'),
  ('47718421-97d8-5065-b913-0e7357c247f0', 'Korea Republic', 'KR'),
  ('9eef204b-964f-5696-8757-1835a387abdb', 'Qatar', 'QA'),
  ('7546a7e8-aed8-5a51-b8f5-8d6516b0ccdc', 'Saudi Arabia', 'SA'),
  ('9b26515e-6869-553c-9687-47bab59a09cf', 'Uzbekistan', 'UZ'),
  ('852beb50-33a4-5a44-a87d-32181ca6d0ad', 'Algeria', 'DZ'),
  ('2e06ab0a-130f-58d3-a2a2-8ab639371e57', 'Cabo Verde', 'CV'),
  ('a9d77cc7-c345-5847-a579-fe6773019d42', 'Congo DR', 'CD'),
  ('eb65fb00-4808-5a68-912b-684fe5c18321', 'Cote d''Ivoire', 'CI'),
  ('b254a63e-85f9-58aa-933e-ce7745565bbf', 'Egypt', 'EG'),
  ('23635794-b7de-5534-819a-3f581440ba04', 'Ghana', 'GH'),
  ('d8b2682c-3eda-539e-bda9-ca70cf1f3b2d', 'Morocco', 'MA'),
  ('3ee63a38-0b88-5376-99d5-135ea4b938b4', 'Senegal', 'SN'),
  ('50b827e8-e628-58aa-b7a0-7a9d50e276e4', 'South Africa', 'ZA'),
  ('f5dac0b6-bc3a-5068-84b4-b943bbe0f6e8', 'Tunisia', 'TN'),
  ('0ece00c5-76a9-5270-9f5a-6be77127a064', 'Curacao', 'CW'),
  ('5a753ec8-1415-54c8-916e-b989f720cfec', 'Haiti', 'HT'),
  ('be314e36-6ece-5f3d-b534-57134e62daba', 'Panama', 'PA'),
  ('9d60d81f-825c-5e86-a724-aa1575769baa', 'Argentina', 'AR'),
  ('7f69d730-e556-5295-9bdc-13d61a62144d', 'Brazil', 'BR'),
  ('48a0af65-b254-5f79-aeaf-5bc8228dd09e', 'Colombia', 'CO'),
  ('c295ab6c-ccd0-5034-8591-32f99958a66c', 'Ecuador', 'EC'),
  ('bb2283bf-4989-583d-8fdc-d8a9f6eadded', 'Paraguay', 'PY'),
  ('f20d0c8e-cf93-5154-9b46-72b66ca82308', 'Uruguay', 'UY'),
  ('54e5d2ac-efb1-54cd-b8a4-95f8dfd64508', 'New Zealand', 'NZ'),
  ('b0aa2056-38a2-59ac-be8f-c558ef913f82', 'Austria', 'AT'),
  ('c89602ee-16e4-5aa9-b7d8-ad31bd85c77d', 'Belgium', 'BE'),
  ('0c478c69-bdae-5e3e-8b42-3494c793e95c', 'Bosnia and Herzegovina', 'BA'),
  ('b1aa27ae-ca0f-5199-a4cf-0e6b5a89e6b0', 'Croatia', 'HR'),
  ('784d045f-ab4b-548a-8ea2-3dc461ea1c7b', 'Czechia', 'CZ'),
  ('3053a231-005a-5023-8a28-5346feea74df', 'England', 'GB'),
  ('f25af76e-9915-5040-92de-9f400c681447', 'France', 'FR'),
  ('0c26de7b-7375-5016-92bb-e2b8f7954592', 'Germany', 'DE'),
  ('fa8af745-cd00-5877-a815-e6e68840c88f', 'Netherlands', 'NL'),
  ('7174879b-faad-5deb-86aa-a9496a18e915', 'Norway', 'NO'),
  ('656015de-13a5-56e9-9b85-8838d215ad15', 'Portugal', 'PT'),
  ('c9686c2f-e56f-5802-b0b9-02e498d83633', 'Scotland', 'GB'),
  ('e9e4c2d0-3cb2-5785-b3a4-797aeca65a33', 'Spain', 'ES'),
  ('2ec21aad-dd53-57b7-909e-a1a69cb91b03', 'Sweden', 'SE'),
  ('8110ff1a-16db-518b-96cf-e96c80f1eef9', 'Switzerland', 'CH'),
  ('d2ffe8ca-6e49-5a3c-a7f8-5426d145293f', 'Turkiye', 'TR')
on conflict (id) do update set
  name = excluded.name,
  country_code = excluded.country_code;

insert into public.players (id, team_id, full_name, position, shirt_number)
values
  ('f8f83aa1-97de-5ca7-82c2-1f52c12b2a01', '968bec99-b07e-5bbf-88c0-37af8fd08da2', 'Alphonso Davies', 'DEF', 19),
  ('5032f877-60f4-5bf6-b4b4-f948750925f2', '968bec99-b07e-5bbf-88c0-37af8fd08da2', 'Jonathan David', 'FWD', 20),
  ('bf1a3b8e-5c81-5f98-a4c9-062d2e7f5401', '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 'Santiago Gimenez', 'FWD', 11),
  ('f456a72d-f29d-55fc-91e8-f758a6483772', '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 'Edson Alvarez', 'MID', 4),
  ('fc34b70b-9102-5bf4-86fd-afcb7304bd44', '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 'Christian Pulisic', 'MID', 10),
  ('8f42b83a-a52e-5b02-9266-cb48e14fb44f', '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 'Tyler Adams', 'MID', 4),
  ('7143a782-f4b7-502f-a8d6-2c7134c36f85', '3b596604-101b-5078-b81f-a0a2d331067b', 'Takefusa Kubo', 'MID', 20),
  ('d39ac5e3-7792-5c72-879a-48d31f6d36f1', '3b596604-101b-5078-b81f-a0a2d331067b', 'Kaoru Mitoma', 'MID', 7)
on conflict (id) do update set
  team_id = excluded.team_id,
  full_name = excluded.full_name,
  position = excluded.position,
  shirt_number = excluded.shirt_number;

insert into public.matches (
  id,
  city_id,
  home_team_id,
  away_team_id,
  competition,
  stage,
  kickoff_time,
  status,
  tags
)
values
  (
    '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101',
    '874c6b46-de32-5014-8e54-da12587a7d7f',
    '968bec99-b07e-5bbf-88c0-37af8fd08da2',
    '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5',
    'FIFA World Cup 2026',
    'group_stage',
    '2026-06-12T23:00:00Z',
    'scheduled',
    array['world-cup', 'group-stage', 'toronto']::text[]
  ),
  (
    'cf319c93-5b02-5ec2-9cc5-7194620ee102',
    '474d6beb-b593-5c05-92c4-a06aa502dbed',
    '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc',
    '3b596604-101b-5078-b81f-a0a2d331067b',
    'FIFA World Cup 2026',
    'group_stage',
    '2026-06-16T02:00:00Z',
    'scheduled',
    array['world-cup', 'group-stage', 'vancouver']::text[]
  )
on conflict (id) do update set
  city_id = excluded.city_id,
  home_team_id = excluded.home_team_id,
  away_team_id = excluded.away_team_id,
  competition = excluded.competition,
  stage = excluded.stage,
  kickoff_time = excluded.kickoff_time,
  status = excluded.status,
  tags = excluded.tags;

insert into public.match_stats (
  match_id,
  team_id,
  goals,
  possession_pct,
  shots,
  shots_on_target,
  passes,
  corners,
  fouls
)
values
  ('1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '968bec99-b07e-5bbf-88c0-37af8fd08da2', 1, 48.50, 11, 4, 435, 5, 12),
  ('1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 1, 51.50, 13, 5, 472, 6, 10),
  ('cf319c93-5b02-5ec2-9cc5-7194620ee102', '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 2, 53.00, 14, 6, 510, 7, 9),
  ('cf319c93-5b02-5ec2-9cc5-7194620ee102', '3b596604-101b-5078-b81f-a0a2d331067b', 1, 47.00, 10, 3, 468, 3, 11)
on conflict (match_id, team_id) do update set
  goals = excluded.goals,
  possession_pct = excluded.possession_pct,
  shots = excluded.shots,
  shots_on_target = excluded.shots_on_target,
  passes = excluded.passes,
  corners = excluded.corners,
  fouls = excluded.fouls,
  updated_at = now();

insert into public.match_events (
  id,
  match_id,
  team_id,
  player_id,
  event_type,
  minute,
  stoppage_minute,
  description
)
values
  ('f4d0ca07-9e1d-5cca-a67d-9564c81b2e01', '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '968bec99-b07e-5bbf-88c0-37af8fd08da2', '5032f877-60f4-5bf6-b4b4-f948750925f2', 'goal', 24, null, 'Canada opens the scoring after a high recovery.'),
  ('33ae3b27-e43e-5687-a5c8-4bde61fca702', '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 'bf1a3b8e-5c81-5f98-a4c9-062d2e7f5401', 'goal', 68, null, 'Mexico equalizes from a central combination.'),
  ('0a52d732-9128-5bf7-bd02-f8cf9088e703', 'cf319c93-5b02-5ec2-9cc5-7194620ee102', '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 'fc34b70b-9102-5bf4-86fd-afcb7304bd44', 'goal', 31, null, 'United States scores after switching play into the right channel.'),
  ('501459e5-8ee7-586c-9614-3a5513761504', 'cf319c93-5b02-5ec2-9cc5-7194620ee102', '3b596604-101b-5078-b81f-a0a2d331067b', '7143a782-f4b7-502f-a8d6-2c7134c36f85', 'yellow_card', 57, null, 'Japan midfielder booked for stopping a transition.')
on conflict (id) do update set
  match_id = excluded.match_id,
  team_id = excluded.team_id,
  player_id = excluded.player_id,
  event_type = excluded.event_type,
  minute = excluded.minute,
  stoppage_minute = excluded.stoppage_minute,
  description = excluded.description;

insert into public.tactical_snapshots (
  id,
  match_id,
  team_id,
  snapshot_minute,
  formation,
  possession_style,
  press_intensity,
  defensive_line,
  confidence
)
values
  ('e4bf8c35-f0a2-5036-b88a-098a1d3e0001', '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '968bec99-b07e-5bbf-88c0-37af8fd08da2', 15, '3-4-2-1', 'direct wide progression', 'high', 'mid', 0.820),
  ('c0f63bd2-adcf-5bff-a3ce-4da3cc620002', '1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101', '5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 15, '4-3-3', 'patient central buildup', 'medium', 'high', 0.790),
  ('9ae0537f-517f-5ff7-b28e-ea79c10a0003', 'cf319c93-5b02-5ec2-9cc5-7194620ee102', '21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 30, '4-2-3-1', 'fast wing isolation', 'high', 'mid', 0.840),
  ('f43405d8-8579-557b-91b7-9de4be520004', 'cf319c93-5b02-5ec2-9cc5-7194620ee102', '3b596604-101b-5078-b81f-a0a2d331067b', 30, '4-2-3-1', 'short combination play', 'medium', 'mid', 0.810)
on conflict (match_id, team_id, snapshot_minute) do update set
  formation = excluded.formation,
  possession_style = excluded.possession_style,
  press_intensity = excluded.press_intensity,
  defensive_line = excluded.defensive_line,
  confidence = excluded.confidence;
