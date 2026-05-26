create extension if not exists pgcrypto;

create table if not exists public.host_cities (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  country_code text not null check (char_length(country_code) = 2),
  stadium_name text null,
  created_at timestamptz not null default now()
);

alter table public.host_cities
add column if not exists stadium_name text null;

create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  country_code text null check (country_code is null or char_length(country_code) = 2),
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text null check (display_name is null or char_length(display_name) <= 50),
  avatar_url text null check (avatar_url is null or char_length(avatar_url) <= 500),
  profile_completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  home_city_id uuid null references public.host_cities(id),
  preferred_match_tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint preferred_match_tags_allowed check (
    preferred_match_tags <@ array[
      'rivalry',
      'high_press',
      'underdog',
      'knockout',
      'fan_festival'
    ]::text[]
  ),
  constraint preferred_match_tags_limit check (
    coalesce(array_length(preferred_match_tags, 1), 0) <= 20
  )
);

create table if not exists public.user_favorite_teams (
  user_id uuid not null references public.profiles(id) on delete cascade,
  team_id uuid not null references public.teams(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, team_id)
);

create index if not exists idx_user_preferences_user_id
  on public.user_preferences(user_id);

create index if not exists idx_user_preferences_home_city_id
  on public.user_preferences(home_city_id);

create index if not exists idx_user_favorite_teams_user_id
  on public.user_favorite_teams(user_id);

create index if not exists idx_user_favorite_teams_team_id
  on public.user_favorite_teams(team_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists set_user_preferences_updated_at on public.user_preferences;
create trigger set_user_preferences_updated_at
before update on public.user_preferences
for each row execute function public.set_updated_at();

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    nullif(trim(new.raw_user_meta_data->>'display_name'), '')
  )
  on conflict (id) do nothing;

  insert into public.user_preferences (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_auth_user();

alter table public.profiles enable row level security;
alter table public.user_preferences enable row level security;
alter table public.user_favorite_teams enable row level security;

alter table public.host_cities enable row level security;
alter table public.teams enable row level security;

drop policy if exists "host cities are publicly readable" on public.host_cities;
create policy "host cities are publicly readable"
on public.host_cities
for select
using (true);

drop policy if exists "teams are publicly readable" on public.teams;
create policy "teams are publicly readable"
on public.teams
for select
using (true);

drop policy if exists "users can read own profile" on public.profiles;
create policy "users can read own profile"
on public.profiles
for select
to authenticated
using (id = auth.uid());

drop policy if exists "users can update own profile" on public.profiles;
create policy "users can update own profile"
on public.profiles
for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

drop policy if exists "users can read own preferences" on public.user_preferences;
create policy "users can read own preferences"
on public.user_preferences
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own preferences" on public.user_preferences;
create policy "users can insert own preferences"
on public.user_preferences
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "users can update own preferences" on public.user_preferences;
create policy "users can update own preferences"
on public.user_preferences
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "users can delete own preferences" on public.user_preferences;
create policy "users can delete own preferences"
on public.user_preferences
for delete
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can read own favorite teams" on public.user_favorite_teams;
create policy "users can read own favorite teams"
on public.user_favorite_teams
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own favorite teams" on public.user_favorite_teams;
create policy "users can insert own favorite teams"
on public.user_favorite_teams
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "users can delete own favorite teams" on public.user_favorite_teams;
create policy "users can delete own favorite teams"
on public.user_favorite_teams
for delete
to authenticated
using (user_id = auth.uid());

insert into public.host_cities (id, name, country_code, stadium_name)
values
  ('874c6b46-de32-5014-8e54-da12587a7d7f', 'Toronto', 'CA', 'BMO Field'),
  ('474d6beb-b593-5c05-92c4-a06aa502dbed', 'Vancouver', 'CA', 'BC Place'),
  ('b671a503-b59c-5d9f-a123-9b1ea8a2c0d6', 'Guadalajara', 'MX', 'Estadio Akron'),
  ('b3a9b5e9-741b-591c-835c-a6f0d06e0f91', 'Mexico City', 'MX', 'Estadio Azteca'),
  ('22a9693c-c752-5a4d-bacc-d2d30e7184b3', 'Monterrey', 'MX', 'Estadio BBVA'),
  ('c50bfe5b-7584-5cbc-986a-3181ad4e24a5', 'Atlanta', 'US', 'Mercedes-Benz Stadium'),
  ('de87922f-8512-5575-90ee-38d8c10282fe', 'Boston', 'US', 'Gillette Stadium'),
  ('b865e6bf-eb90-593f-aa76-7ffb55fd9fda', 'Dallas', 'US', 'AT&T Stadium'),
  ('713d1905-0f40-57b5-84fc-4409f300c919', 'Houston', 'US', 'NRG Stadium'),
  ('4da740f5-55c8-53a1-bc01-2f16e943110d', 'Kansas City', 'US', 'GEHA Field at Arrowhead Stadium'),
  ('8b2dc317-8b49-5b8a-8544-7d091044b4e1', 'Los Angeles', 'US', 'SoFi Stadium'),
  ('bd337c08-d7f9-57bb-8a33-c2feeb3ca18f', 'Miami', 'US', 'Hard Rock Stadium'),
  ('e0452c84-d22b-54b2-9f48-6805f73801c6', 'New York/NJ', 'US', 'MetLife Stadium'),
  ('4d1935bc-b2b5-5ebf-9ea9-36ba368d8972', 'Philadelphia', 'US', 'Lincoln Financial Field'),
  ('cc33e2c4-6c1c-5d5b-8985-6015ed027a07', 'San Francisco Bay Area', 'US', 'Levi''s Stadium'),
  ('e5fae842-3ec7-5636-a2ae-ebb90793ee85', 'Seattle', 'US', 'Lumen Field')
on conflict (id) do update set
  name = excluded.name,
  country_code = excluded.country_code,
  stadium_name = excluded.stadium_name;

insert into public.teams (id, name, country_code)
values
  ('968bec99-b07e-5bbf-88c0-37af8fd08da2', 'Canada', null),
  ('5baedb39-9cd5-5a02-8b25-9f9c8420c7a5', 'Mexico', null),
  ('21b21503-e79e-5fc5-b42c-c0d8ed07f7dc', 'United States', null),
  ('b0aa2056-38a2-59ac-be8f-c558ef913f82', 'Austria', null),
  ('c89602ee-16e4-5aa9-b7d8-ad31bd85c77d', 'Belgium', null),
  ('0c478c69-bdae-5e3e-8b42-3494c793e95c', 'Bosnia and Herzegovina', null),
  ('b1aa27ae-ca0f-5199-a4cf-0e6b5a89e6b0', 'Croatia', null),
  ('784d045f-ab4b-548a-8ea2-3dc461ea1c7b', 'Czechia', null),
  ('3053a231-005a-5023-8a28-5346feea74df', 'England', null),
  ('f25af76e-9915-5040-92de-9f400c681447', 'France', null),
  ('0c26de7b-7375-5016-92bb-e2b8f7954592', 'Germany', null),
  ('fa8af745-cd00-5877-a815-e6e68840c88f', 'Netherlands', null),
  ('7174879b-faad-5deb-86aa-a9496a18e915', 'Norway', null),
  ('656015de-13a5-56e9-9b85-8838d215ad15', 'Portugal', null),
  ('c9686c2f-e56f-5802-b0b9-02e498d83633', 'Scotland', null),
  ('e9e4c2d0-3cb2-5785-b3a4-797aeca65a33', 'Spain', null),
  ('2ec21aad-dd53-57b7-909e-a1a69cb91b03', 'Sweden', null),
  ('8110ff1a-16db-518b-96cf-e96c80f1eef9', 'Switzerland', null),
  ('d2ffe8ca-6e49-5a3c-a7f8-5426d145293f', 'Türkiye', null),
  ('9d60d81f-825c-5e86-a724-aa1575769baa', 'Argentina', null),
  ('7f69d730-e556-5295-9bdc-13d61a62144d', 'Brazil', null),
  ('48a0af65-b254-5f79-aeaf-5bc8228dd09e', 'Colombia', null),
  ('c295ab6c-ccd0-5034-8591-32f99958a66c', 'Ecuador', null),
  ('bb2283bf-4989-583d-8fdc-d8a9f6eadded', 'Paraguay', null),
  ('f20d0c8e-cf93-5154-9b46-72b66ca82308', 'Uruguay', null),
  ('852beb50-33a4-5a44-a87d-32181ca6d0ad', 'Algeria', null),
  ('2e06ab0a-130f-58d3-a2a2-8ab639371e57', 'Cabo Verde', null),
  ('a9d77cc7-c345-5847-a579-fe6773019d42', 'Congo DR', null),
  ('eb65fb00-4808-5a68-912b-684fe5c18321', 'Côte d''Ivoire', null),
  ('b254a63e-85f9-58aa-933e-ce7745565bbf', 'Egypt', null),
  ('23635794-b7de-5534-819a-3f581440ba04', 'Ghana', null),
  ('d8b2682c-3eda-539e-bda9-ca70cf1f3b2d', 'Morocco', null),
  ('3ee63a38-0b88-5376-99d5-135ea4b938b4', 'Senegal', null),
  ('50b827e8-e628-58aa-b7a0-7a9d50e276e4', 'South Africa', null),
  ('f5dac0b6-bc3a-5068-84b4-b943bbe0f6e8', 'Tunisia', null),
  ('91a1a6ae-6a33-50bd-855f-e6f054ccfdab', 'Australia', null),
  ('21415ca8-4840-5a23-b60c-db3a88f2f7c1', 'IR Iran', null),
  ('6e45bc34-588b-5fa6-bc54-31076a776b82', 'Iraq', null),
  ('3b596604-101b-5078-b81f-a0a2d331067b', 'Japan', null),
  ('e67134d3-0ffa-5bad-be66-15a7760fedda', 'Jordan', null),
  ('47718421-97d8-5065-b913-0e7357c247f0', 'Korea Republic', null),
  ('9eef204b-964f-5696-8757-1835a387abdb', 'Qatar', null),
  ('7546a7e8-aed8-5a51-b8f5-8d6516b0ccdc', 'Saudi Arabia', null),
  ('9b26515e-6869-553c-9687-47bab59a09cf', 'Uzbekistan', null),
  ('0ece00c5-76a9-5270-9f5a-6be77127a064', 'Curaçao', null),
  ('5a753ec8-1415-54c8-916e-b989f720cfec', 'Haiti', null),
  ('be314e36-6ece-5f3d-b534-57134e62daba', 'Panama', null),
  ('54e5d2ac-efb1-54cd-b8a4-95f8dfd64508', 'New Zealand', null)
on conflict (id) do nothing;

update public.user_preferences
set home_city_id = null
where home_city_id in (
  '11111111-1111-1111-1111-111111111111',
  '11111111-1111-1111-1111-111111111112',
  '11111111-1111-1111-1111-111111111113'
);

delete from public.host_cities
where id in (
  '11111111-1111-1111-1111-111111111111',
  '11111111-1111-1111-1111-111111111112',
  '11111111-1111-1111-1111-111111111113'
);

delete from public.teams
where id in (
  '22222222-2222-2222-2222-222222222222',
  '22222222-2222-2222-2222-222222222223',
  '22222222-2222-2222-2222-222222222224',
  '22222222-2222-2222-2222-222222222225'
);
