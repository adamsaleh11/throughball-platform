create table if not exists public.itineraries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  city_id uuid not null references public.host_cities(id) on delete restrict,
  match_id uuid null references public.matches(id) on delete set null,
  input_hash text not null,
  input_payload jsonb not null,
  title text not null check (char_length(title) <= 120),
  summary text null check (summary is null or char_length(summary) <= 1000),
  status text not null default 'saved' check (status in ('saved')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, input_hash)
);

create table if not exists public.itinerary_items (
  id uuid primary key default gen_random_uuid(),
  itinerary_id uuid not null references public.itineraries(id) on delete cascade,
  position integer not null check (position >= 1),
  item_type text not null check (char_length(item_type) <= 50),
  source_table text null check (
    source_table is null or source_table in (
      'venues',
      'city_events',
      'tourist_spots',
      'transport_hubs'
    )
  ),
  source_id uuid null,
  title text not null check (char_length(title) <= 160),
  description text null check (description is null or char_length(description) <= 1500),
  starts_at timestamptz null,
  ends_at timestamptz null,
  area_label text null check (area_label is null or char_length(area_label) <= 120),
  route_context jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (itinerary_id, position)
);

create index if not exists idx_itineraries_user_updated
  on public.itineraries(user_id, updated_at desc, created_at desc);

create index if not exists idx_itineraries_city
  on public.itineraries(city_id);

create index if not exists idx_itinerary_items_itinerary_position
  on public.itinerary_items(itinerary_id, position);

drop trigger if exists set_itineraries_updated_at on public.itineraries;
create trigger set_itineraries_updated_at
before update on public.itineraries
for each row execute function public.set_updated_at();

alter table public.itineraries enable row level security;
alter table public.itinerary_items enable row level security;

drop policy if exists "users can read own itineraries" on public.itineraries;
create policy "users can read own itineraries"
on public.itineraries
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can insert own itineraries" on public.itineraries;
create policy "users can insert own itineraries"
on public.itineraries
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "users can update own itineraries" on public.itineraries;
create policy "users can update own itineraries"
on public.itineraries
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "users can delete own itineraries" on public.itineraries;
create policy "users can delete own itineraries"
on public.itineraries
for delete
to authenticated
using (user_id = auth.uid());

drop policy if exists "users can read own itinerary items" on public.itinerary_items;
create policy "users can read own itinerary items"
on public.itinerary_items
for select
to authenticated
using (auth.uid() = (select user_id from public.itineraries where id = itinerary_id));

drop policy if exists "users can insert own itinerary items" on public.itinerary_items;
create policy "users can insert own itinerary items"
on public.itinerary_items
for insert
to authenticated
with check (auth.uid() = (select user_id from public.itineraries where id = itinerary_id));

drop policy if exists "users can update own itinerary items" on public.itinerary_items;
create policy "users can update own itinerary items"
on public.itinerary_items
for update
to authenticated
using (auth.uid() = (select user_id from public.itineraries where id = itinerary_id))
with check (auth.uid() = (select user_id from public.itineraries where id = itinerary_id));

drop policy if exists "users can delete own itinerary items" on public.itinerary_items;
create policy "users can delete own itinerary items"
on public.itinerary_items
for delete
to authenticated
using (auth.uid() = (select user_id from public.itineraries where id = itinerary_id));
