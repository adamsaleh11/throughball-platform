create table if not exists public.venues (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete cascade,
  name text not null,
  venue_type text not null,
  area_label text null,
  latitude numeric(9,6) null,
  longitude numeric(9,6) null,
  location_precision text null,
  capacity_estimate integer null check (capacity_estimate is null or capacity_estimate >= 0),
  amenities text[] not null default '{}',
  tags text[] not null default '{}',
  source_name text not null,
  source_url text not null,
  data_origin text not null,
  last_verified_at date not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.city_events (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete cascade,
  title text not null,
  event_type text not null,
  area_label text null,
  starts_at timestamptz null,
  ends_at timestamptz null,
  tags text[] not null default '{}',
  source_name text not null,
  source_url text not null,
  data_origin text not null,
  last_verified_at date not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tourist_spots (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete cascade,
  name text not null,
  spot_type text not null,
  area_label text null,
  latitude numeric(9,6) null,
  longitude numeric(9,6) null,
  location_precision text null,
  tags text[] not null default '{}',
  source_name text not null,
  source_url text not null,
  data_origin text not null,
  last_verified_at date not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.transport_hubs (
  id uuid primary key default gen_random_uuid(),
  city_id uuid not null references public.host_cities(id) on delete cascade,
  name text not null,
  hub_type text not null,
  area_label text null,
  latitude numeric(9,6) null,
  longitude numeric(9,6) null,
  location_precision text null,
  tags text[] not null default '{}',
  source_name text not null,
  source_url text not null,
  data_origin text not null,
  last_verified_at date not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_venues_city_type on public.venues(city_id, venue_type);
create index if not exists idx_city_events_city_type_starts on public.city_events(city_id, event_type, starts_at);
create index if not exists idx_tourist_spots_city_type on public.tourist_spots(city_id, spot_type);
create index if not exists idx_transport_hubs_city_type on public.transport_hubs(city_id, hub_type);

alter table public.venues enable row level security;
alter table public.city_events enable row level security;
alter table public.tourist_spots enable row level security;
alter table public.transport_hubs enable row level security;

drop policy if exists "venues are publicly readable" on public.venues;
create policy "venues are publicly readable"
on public.venues
for select
using (true);

drop policy if exists "city events are publicly readable" on public.city_events;
create policy "city events are publicly readable"
on public.city_events
for select
using (true);

drop policy if exists "tourist spots are publicly readable" on public.tourist_spots;
create policy "tourist spots are publicly readable"
on public.tourist_spots
for select
using (true);

drop policy if exists "transport hubs are publicly readable" on public.transport_hubs;
create policy "transport hubs are publicly readable"
on public.transport_hubs
for select
using (true);

insert into public.venues (
  id, city_id, name, venue_type, area_label, latitude, longitude, location_precision,
  capacity_estimate, amenities, tags, source_name, source_url, data_origin, last_verified_at
)
values
  ('84e15095-1629-5552-8750-8ab15a93ff96','874c6b46-de32-5014-8e54-da12587a7d7f','BMO Field','stadium','Exhibition Place',43.633200,-79.418600,'exact_public_place',45000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('bab34a20-0c60-5b1d-a292-c7988cf91114','474d6beb-b593-5c05-92c4-a06aa502dbed','BC Place','stadium','Downtown Vancouver',49.276700,-123.111900,'exact_public_place',54000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('77fcd755-832b-5726-b3ff-09a84e5cd492','b671a503-b59c-5d9f-a123-9b1ea8a2c0d6','Estadio Akron','stadium','Zapopan',20.681900,-103.462800,'exact_public_place',48000,'{transit_access}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('48b1666d-3409-540a-9d6d-c2f6d72de6e3','b3a9b5e9-741b-591c-835c-a6f0d06e0f91','Estadio Azteca','stadium','Coyoacan',19.302900,-99.150500,'exact_public_place',87500,'{transit_access}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('85f58402-82f6-55aa-92e5-3c100c6a214f','22a9693c-c752-5a4d-bacc-d2d30e7184b3','Estadio BBVA','stadium','Guadalupe',25.668300,-100.244700,'exact_public_place',53500,'{transit_access}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('017ffeb5-542e-5d49-af60-439085b0d0ed','c50bfe5b-7584-5cbc-986a-3181ad4e24a5','Mercedes-Benz Stadium','stadium','Downtown Atlanta',33.755400,-84.400800,'exact_public_place',71000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('c43dfdc5-c989-5e76-a84d-29869012d8e3','de87922f-8512-5575-90ee-38d8c10282fe','Gillette Stadium','stadium','Foxborough',42.090900,-71.264300,'exact_public_place',65000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('9d957403-fcdf-54b8-b21d-baa6b49f8a33','b865e6bf-eb90-593f-aa76-7ffb55fd9fda','AT&T Stadium','stadium','Arlington',32.747300,-97.094500,'exact_public_place',94000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('d56284a6-cf0f-5656-aa8c-ad70cc31ef01','713d1905-0f40-57b5-84fc-4409f300c919','NRG Stadium','stadium','NRG Park',29.684700,-95.410700,'exact_public_place',72000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('08fb7db1-d634-515f-89e2-c5875e27cdd3','4da740f5-55c8-53a1-bc01-2f16e943110d','GEHA Field at Arrowhead Stadium','stadium','Truman Sports Complex',39.048900,-94.483900,'exact_public_place',73000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('876021fb-76ff-5d95-b202-07cbf9857aca','8b2dc317-8b49-5b8a-8544-7d091044b4e1','SoFi Stadium','stadium','Inglewood',33.953500,-118.339200,'exact_public_place',70000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('f5efa073-f30c-50ba-91ec-05dec5b4ab2b','bd337c08-d7f9-57bb-8a33-c2feeb3ca18f','Hard Rock Stadium','stadium','Miami Gardens',25.958000,-80.238900,'exact_public_place',65000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('42f6ef92-990d-5486-8011-55603ced7cb9','e0452c84-d22b-54b2-9f48-6805f73801c6','MetLife Stadium','stadium','East Rutherford',40.813500,-74.074500,'exact_public_place',82500,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('bbcf29ac-8396-5499-b9b3-f3433978cd95','4d1935bc-b2b5-5ebf-9ea9-36ba368d8972','Lincoln Financial Field','stadium','South Philadelphia',39.900800,-75.167500,'exact_public_place',69000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('02374358-60e6-5b29-8c7d-3c5b8d77b1ad','cc33e2c4-6c1c-5d5b-8985-6015ed027a07','Levi''s Stadium','stadium','Santa Clara',37.403000,-121.970000,'exact_public_place',71000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('e127b15e-fa64-5daa-a6fb-627852b28ce6','e5fae842-3ec7-5636-a2ae-ebb90793ee85','Lumen Field','stadium','SoDo',47.595200,-122.331600,'exact_public_place',69000,'{transit_access,accessible}','{world-cup,stadium}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28')
on conflict (id) do update set
  name = excluded.name,
  venue_type = excluded.venue_type,
  area_label = excluded.area_label,
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  location_precision = excluded.location_precision,
  capacity_estimate = excluded.capacity_estimate,
  amenities = excluded.amenities,
  tags = excluded.tags,
  source_name = excluded.source_name,
  source_url = excluded.source_url,
  data_origin = excluded.data_origin,
  last_verified_at = excluded.last_verified_at;

insert into public.city_events (
  id, city_id, title, event_type, area_label, starts_at, ends_at, tags,
  source_name, source_url, data_origin, last_verified_at
)
values
  ('853ecec6-f59d-5a7a-8d6c-c6921136f882','874c6b46-de32-5014-8e54-da12587a7d7f','FIFA World Cup 26 Toronto Host City','world_cup_hosting','BMO Field','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('acb40f5d-d985-591c-ab7f-e0e4ba6725b6','474d6beb-b593-5c05-92c4-a06aa502dbed','FIFA World Cup 26 Vancouver Host City','world_cup_hosting','BC Place','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('1c0a0c04-dd74-532a-ac1d-c82d856f9489','b671a503-b59c-5d9f-a123-9b1ea8a2c0d6','FIFA World Cup 26 Guadalajara Host City','world_cup_hosting','Estadio Akron','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('e0502017-29e9-5e7b-a5ba-d7e2b4623bc1','b3a9b5e9-741b-591c-835c-a6f0d06e0f91','FIFA World Cup 26 Mexico City Host City','world_cup_hosting','Estadio Azteca','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('e8c5f9f6-c093-5bf9-b97c-98ccfdcecadb','22a9693c-c752-5a4d-bacc-d2d30e7184b3','FIFA World Cup 26 Monterrey Host City','world_cup_hosting','Estadio BBVA','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('1f0a962c-bcd3-5ac7-b941-1bb56ba52804','c50bfe5b-7584-5cbc-986a-3181ad4e24a5','FIFA World Cup 26 Atlanta Host City','world_cup_hosting','Mercedes-Benz Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('18cd8823-3c4c-5802-8edb-23b777a78cc8','de87922f-8512-5575-90ee-38d8c10282fe','FIFA World Cup 26 Boston Host City','world_cup_hosting','Gillette Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('2d7cdd38-57fb-5e8b-9688-f738ef845e75','b865e6bf-eb90-593f-aa76-7ffb55fd9fda','FIFA World Cup 26 Dallas Host City','world_cup_hosting','AT&T Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('9330f053-48d9-50dd-b187-c0ca6cd00971','713d1905-0f40-57b5-84fc-4409f300c919','FIFA World Cup 26 Houston Host City','world_cup_hosting','NRG Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('a715f182-2d88-5ff0-ae35-e47cf64d0ba9','4da740f5-55c8-53a1-bc01-2f16e943110d','FIFA World Cup 26 Kansas City Host City','world_cup_hosting','GEHA Field at Arrowhead Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('c82e8b29-8c8b-5f6a-9cbb-9eed1e46ef82','8b2dc317-8b49-5b8a-8544-7d091044b4e1','FIFA World Cup 26 Los Angeles Host City','world_cup_hosting','SoFi Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('6f434738-5864-5c51-af4f-728fba5082a9','bd337c08-d7f9-57bb-8a33-c2feeb3ca18f','FIFA World Cup 26 Miami Host City','world_cup_hosting','Hard Rock Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('7a1b65fa-c49b-52be-9d99-94af081f0f34','e0452c84-d22b-54b2-9f48-6805f73801c6','FIFA World Cup 26 New York/New Jersey Host City','world_cup_hosting','MetLife Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('55f2a8ee-bf2e-5e1e-a82c-409095292cd3','4d1935bc-b2b5-5ebf-9ea9-36ba368d8972','FIFA World Cup 26 Philadelphia Host City','world_cup_hosting','Lincoln Financial Field','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('299b6cfd-9378-5f94-bcd6-7677fcccc144','cc33e2c4-6c1c-5d5b-8985-6015ed027a07','FIFA World Cup 26 San Francisco Bay Area Host City','world_cup_hosting','Levi''s Stadium','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28'),
  ('bdbef0d5-93ab-5643-bb73-fe66f76d94e9','e5fae842-3ec7-5636-a2ae-ebb90793ee85','FIFA World Cup 26 Seattle Host City','world_cup_hosting','Lumen Field','2026-06-11T00:00:00Z','2026-07-19T23:59:59Z','{world-cup,host-city}','FIFA World Cup 26','https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026','official_site','2026-05-28')
on conflict (id) do update set
  title = excluded.title,
  event_type = excluded.event_type,
  area_label = excluded.area_label,
  starts_at = excluded.starts_at,
  ends_at = excluded.ends_at,
  tags = excluded.tags,
  source_name = excluded.source_name,
  source_url = excluded.source_url,
  data_origin = excluded.data_origin,
  last_verified_at = excluded.last_verified_at;

insert into public.tourist_spots (
  id, city_id, name, spot_type, area_label, latitude, longitude, location_precision,
  tags, source_name, source_url, data_origin, last_verified_at
)
values
  ('7cb6f0e1-ac0d-5a4c-bfd2-433829ddb7a5','874c6b46-de32-5014-8e54-da12587a7d7f','CN Tower','landmark','Downtown',43.642600,-79.387100,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q183251','wikidata','2026-05-28'),
  ('e6990a30-0a3a-5da2-84aa-538fc5f05158','474d6beb-b593-5c05-92c4-a06aa502dbed','Stanley Park','park','West End',49.304300,-123.144300,'exact_public_place','{park,landmark}','Wikidata','https://www.wikidata.org/wiki/Q237367','wikidata','2026-05-28'),
  ('afc78e2e-fe47-5979-9e88-b9f161f9c049','b671a503-b59c-5d9f-a123-9b1ea8a2c0d6','Guadalajara Cathedral','landmark','Centro',20.676700,-103.347500,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q748338','wikidata','2026-05-28'),
  ('820e065d-f013-5a38-912e-dd4ede664f91','b3a9b5e9-741b-591c-835c-a6f0d06e0f91','Palacio de Bellas Artes','landmark','Centro Historico',19.435200,-99.141200,'exact_public_place','{landmark,museum}','Wikidata','https://www.wikidata.org/wiki/Q205663','wikidata','2026-05-28'),
  ('58b9a5a3-cf37-59f7-9c5c-36f5499d4a2c','22a9693c-c752-5a4d-bacc-d2d30e7184b3','Macroplaza','landmark','Centro',25.669700,-100.309900,'exact_public_place','{landmark,public-space}','Wikidata','https://www.wikidata.org/wiki/Q672099','wikidata','2026-05-28'),
  ('2f5ab39f-10dc-5e3f-921a-290f0544e158','c50bfe5b-7584-5cbc-986a-3181ad4e24a5','Centennial Olympic Park','park','Downtown Atlanta',33.760300,-84.393800,'exact_public_place','{park,landmark}','Wikidata','https://www.wikidata.org/wiki/Q1056862','wikidata','2026-05-28'),
  ('7e79e986-c520-5c83-8529-d853f18271f5','de87922f-8512-5575-90ee-38d8c10282fe','Boston Common','park','Downtown Boston',42.355000,-71.065600,'exact_public_place','{park,landmark}','Wikidata','https://www.wikidata.org/wiki/Q671843','wikidata','2026-05-28'),
  ('51755770-b8d8-5baa-9188-a223488a8594','b865e6bf-eb90-593f-aa76-7ffb55fd9fda','Dealey Plaza','landmark','Downtown Dallas',32.778800,-96.808300,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q1182078','wikidata','2026-05-28'),
  ('7fab3108-9b2e-50dd-bd4a-e08198a7d667','713d1905-0f40-57b5-84fc-4409f300c919','Space Center Houston','museum','Clear Lake',29.550200,-95.097000,'exact_public_place','{museum,landmark}','Wikidata','https://www.wikidata.org/wiki/Q1759001','wikidata','2026-05-28'),
  ('c25d5df3-a112-5f99-bae2-6ded246d76e7','4da740f5-55c8-53a1-bc01-2f16e943110d','National WWI Museum and Memorial','museum','Crown Center',39.080600,-94.586000,'exact_public_place','{museum,landmark}','Wikidata','https://www.wikidata.org/wiki/Q6976194','wikidata','2026-05-28'),
  ('39c63b6d-0867-5444-8e28-4f30b07b87fd','8b2dc317-8b49-5b8a-8544-7d091044b4e1','Griffith Observatory','landmark','Griffith Park',34.118400,-118.300400,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q842839','wikidata','2026-05-28'),
  ('abe136b1-f328-5768-a712-716f8d5408e6','bd337c08-d7f9-57bb-8a33-c2feeb3ca18f','Bayfront Park','park','Downtown Miami',25.775300,-80.186900,'exact_public_place','{park,landmark}','Wikidata','https://www.wikidata.org/wiki/Q812574','wikidata','2026-05-28'),
  ('1abbc8c7-4935-5446-bb8e-8ee89c6040ce','e0452c84-d22b-54b2-9f48-6805f73801c6','Statue of Liberty','landmark','New York Harbor',40.689200,-74.044500,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q9202','wikidata','2026-05-28'),
  ('4af992ea-e56f-52df-95ca-a7f95f0d0833','4d1935bc-b2b5-5ebf-9ea9-36ba368d8972','Independence Hall','landmark','Old City',39.948900,-75.150000,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q37100','wikidata','2026-05-28'),
  ('61bb89ba-6363-564e-ae92-a04fd8e3aed9','cc33e2c4-6c1c-5d5b-8985-6015ed027a07','Golden Gate Bridge','landmark','Golden Gate',37.819900,-122.478300,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q44440','wikidata','2026-05-28'),
  ('00dd159e-5787-5565-be45-2c090e2220dc','e5fae842-3ec7-5636-a2ae-ebb90793ee85','Space Needle','landmark','Seattle Center',47.620500,-122.349300,'exact_public_place','{landmark}','Wikidata','https://www.wikidata.org/wiki/Q44450','wikidata','2026-05-28')
on conflict (id) do update set
  name = excluded.name,
  spot_type = excluded.spot_type,
  area_label = excluded.area_label,
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  location_precision = excluded.location_precision,
  tags = excluded.tags,
  source_name = excluded.source_name,
  source_url = excluded.source_url,
  data_origin = excluded.data_origin,
  last_verified_at = excluded.last_verified_at;

insert into public.transport_hubs (
  id, city_id, name, hub_type, area_label, latitude, longitude, location_precision,
  tags, source_name, source_url, data_origin, last_verified_at
)
values
  ('da45633e-9c1e-53d2-b00a-83ecd4973c2f','874c6b46-de32-5014-8e54-da12587a7d7f','Toronto Pearson International Airport','airport','Mississauga',43.677700,-79.624800,'exact_public_place','{airport}','Wikidata','https://www.wikidata.org/wiki/Q32191','wikidata','2026-05-28'),
  ('6ed50ce8-e3fc-5e46-a0bd-3b089f36fc72','474d6beb-b593-5c05-92c4-a06aa502dbed','Vancouver International Airport','airport','Richmond',49.196700,-123.181500,'exact_public_place','{airport}','Official airport site','https://www.yvr.ca/','official_site','2026-05-28'),
  ('3056a53c-bfde-5e65-b8ac-43b891feb15d','b671a503-b59c-5d9f-a123-9b1ea8a2c0d6','Miguel Hidalgo y Costilla Guadalajara International Airport','airport','Tlajomulco de Zuniga',20.521800,-103.311200,'exact_public_place','{airport}','Official airport site','https://www.aeropuertosgap.com.mx/en/guadalajara-3.html','official_site','2026-05-28'),
  ('319a4894-3c67-50a0-a864-09898ddabb6b','b3a9b5e9-741b-591c-835c-a6f0d06e0f91','Mexico City International Airport','airport','Venustiano Carranza',19.436100,-99.071900,'exact_public_place','{airport}','Official airport site','https://www.aicm.com.mx/','official_site','2026-05-28'),
  ('055a691c-550c-54aa-848e-2f640065f5de','22a9693c-c752-5a4d-bacc-d2d30e7184b3','Monterrey International Airport','airport','Apodaca',25.778500,-100.107000,'exact_public_place','{airport}','Official airport site','https://www.oma.aero/en/passengers/monterrey/','official_site','2026-05-28'),
  ('ac07d87e-f222-5536-aac9-1dc57120816a','c50bfe5b-7584-5cbc-986a-3181ad4e24a5','Hartsfield-Jackson Atlanta International Airport','airport','College Park',33.640700,-84.427700,'exact_public_place','{airport}','Official airport site','https://www.atl.com/','official_site','2026-05-28'),
  ('7f81155e-b16b-5d5c-8a4d-35633bb208d0','de87922f-8512-5575-90ee-38d8c10282fe','Logan International Airport','airport','East Boston',42.365600,-71.009600,'exact_public_place','{airport}','Official airport site','https://www.massport.com/logan-airport','official_site','2026-05-28'),
  ('cc0a8f0f-206c-5c09-95f5-b592eb60454b','b865e6bf-eb90-593f-aa76-7ffb55fd9fda','Dallas Fort Worth International Airport','airport','DFW Airport',32.899800,-97.040300,'exact_public_place','{airport}','Official airport site','https://www.dfwairport.com/','official_site','2026-05-28'),
  ('94d7ddb8-f6fe-59e3-90e4-87261e9711c0','713d1905-0f40-57b5-84fc-4409f300c919','George Bush Intercontinental Airport','airport','North Houston',29.990200,-95.336800,'exact_public_place','{airport}','Official airport site','https://www.fly2houston.com/iah/overview','official_site','2026-05-28'),
  ('19d2ec97-0da5-503e-ada9-1905faf3a481','4da740f5-55c8-53a1-bc01-2f16e943110d','Kansas City International Airport','airport','Platte County',39.297600,-94.713900,'exact_public_place','{airport}','Official airport site','https://flykc.com/','official_site','2026-05-28'),
  ('29d0b598-9eb2-5e6d-8f9f-1421f8c219d5','8b2dc317-8b49-5b8a-8544-7d091044b4e1','Los Angeles International Airport','airport','Westchester',33.941600,-118.408500,'exact_public_place','{airport}','Official airport site','https://www.flylax.com/','official_site','2026-05-28'),
  ('819e87e4-9530-59d1-89e0-03da0a948389','bd337c08-d7f9-57bb-8a33-c2feeb3ca18f','Miami International Airport','airport','Miami',25.795900,-80.287000,'exact_public_place','{airport}','Official airport site','https://www.miami-airport.com/','official_site','2026-05-28'),
  ('e983a962-4e57-5ab6-8b97-b30f9076354e','e0452c84-d22b-54b2-9f48-6805f73801c6','Newark Liberty International Airport','airport','Newark',40.689500,-74.174500,'exact_public_place','{airport}','Official airport site','https://www.newarkairport.com/','official_site','2026-05-28'),
  ('987c6c9b-86cf-5b03-ab96-8401e2aa20ea','4d1935bc-b2b5-5ebf-9ea9-36ba368d8972','Philadelphia International Airport','airport','Southwest Philadelphia',39.874400,-75.242400,'exact_public_place','{airport}','Official airport site','https://www.phl.org/','official_site','2026-05-28'),
  ('68eda754-b3c1-5982-b2a5-619a454577c8','cc33e2c4-6c1c-5d5b-8985-6015ed027a07','San Francisco International Airport','airport','San Mateo County',37.621300,-122.379000,'exact_public_place','{airport}','Official airport site','https://www.flysfo.com/','official_site','2026-05-28'),
  ('3fc6a1cc-85eb-5ff7-a152-02a015bb52b0','e5fae842-3ec7-5636-a2ae-ebb90793ee85','Seattle-Tacoma International Airport','airport','SeaTac',47.450200,-122.308800,'exact_public_place','{airport}','Official airport site','https://www.portseattle.org/sea-tac','official_site','2026-05-28')
on conflict (id) do update set
  name = excluded.name,
  hub_type = excluded.hub_type,
  area_label = excluded.area_label,
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  location_precision = excluded.location_precision,
  tags = excluded.tags,
  source_name = excluded.source_name,
  source_url = excluded.source_url,
  data_origin = excluded.data_origin,
  last_verified_at = excluded.last_verified_at;
