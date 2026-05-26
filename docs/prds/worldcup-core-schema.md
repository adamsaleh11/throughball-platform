# World Cup Core Schema PRD

## Problem Statement

Throughball needs a deterministic World Cup data foundation in Supabase Postgres so the backend and demo frontend can query host cities, countries/teams, matches, match stats, match events, and tactical snapshots without relying on paid sports APIs or live polling. The current repo already has early `host_cities` and `teams` tables for auth/onboarding, but the platform lacks the broader match-domain schema required for World Cup demo flows.

This matters now because later recommendation, hotspot, itinerary, and operational demo features need stable seeded sports data. The backend should rank, filter, aggregate, and explain known data; it should not ask an AI system or an external sports provider to invent fixtures, teams, or tactical context.

## Solution

Create an additive Supabase migration that extends the existing public domain tables and adds the core World Cup tables: `players`, `matches`, `match_stats`, `match_events`, and `tactical_snapshots`. The migration must be repeatable and safe to rerun by using idempotent table, column, index, policy, and seed patterns.

The seed layer must include all FIFA World Cup 2026 host cities and all participating countries/teams as reference data. Seeded demo match data remains intentionally small: Toronto and Vancouver must be represented first, with a handful of realistic seeded matches, players, stats, events, and tactical snapshots sufficient for local demo flows. The system must not connect to paid sports APIs, ingest large live feeds, or run polling jobs.

FastAPI should be able to query cities and matches through lightweight read endpoints that follow the existing API contract style and include observability metadata. These routes should tolerate missing Supabase configuration in local health/build contexts while making the missing dependency clear when domain data is requested.

## User Stories

1. As a demo user, I want to see World Cup host cities, so that I can browse location-based match experiences.
2. As a demo user, I want Toronto and Vancouver to appear in seeded data, so that Canadian host-city flows can be demonstrated first.
3. As a demo user, I want all World Cup host cities to exist as reference data, so that the app can support later city filters without another schema rewrite.
4. As a demo user, I want all participating countries/teams to exist as reference data, so that onboarding and match demos are not limited to a tiny subset.
5. As a demo user, I want to list matches by city, so that I can discover what is happening near a host city.
6. As a demo user, I want match cards to include teams, competition, kickoff time, status, and tags, so that seeded demos feel realistic.
7. As a backend developer, I want a normalized `matches` table with city and team references, so that queries can be deterministic and indexable.
8. As a backend developer, I want players linked to teams, so that seeded match events can reference realistic roster data.
9. As a backend developer, I want match stats stored one row per team per match, so that deterministic comparisons can be computed without AI synthesis.
10. As a backend developer, I want match events stored as structured rows, so that timelines can be queried and rendered without parsing free text.
11. As a backend developer, I want tactical snapshots stored as structured rows, so that analysis features can explain known tactical context without inventing it.
12. As a backend developer, I want migrations to be repeatable, so that local and hosted Supabase environments can be repaired or reapplied safely.
13. As a backend developer, I want indexes on city, team, match, and kickoff query paths, so that common demo endpoints remain low latency.
14. As a backend developer, I want seed data to load with the migration, so that the demo can run immediately after applying database changes.
15. As an operator, I want public sports reference tables to be readable but not writable by client users, so that demo data is stable.
16. As an operator, I want no paid sports API integration in this ticket, so that costs remain predictable and local-first development stays intact.
17. As an operator, I want no live polling jobs in this ticket, so that there is no always-on operational cost.
18. As an API consumer, I want city and match responses to include request metadata, so that backend calls remain traceable.
19. As a tester, I want mocked backend tests for city and match queries, so that normal test runs do not depend on hosted Supabase.
20. As a tester, I want migration acceptance checks documented, so that Supabase schema changes can be validated consistently.

## Implementation Decisions

- Add a new additive Supabase migration instead of rewriting the existing auth/profile migration.
- Reuse existing `host_cities` and `teams` tables because onboarding and profile preferences already depend on them.
- Extend `host_cities` with only demo-needed fields such as `timezone` and `updated_at`.
- Extend `teams` with only demo-needed fields such as `group_code`, `fifa_ranking`, and `updated_at`.
- Use UUID primary keys with `gen_random_uuid()` defaults and deterministic UUID values for seeded rows.
- Do not add external sports-provider IDs in this ticket unless needed for seeded demo flows.
- Create the exact domain tables named in the ticket: `host_cities`, `teams`, `players`, `matches`, `match_stats`, `match_events`, and `tactical_snapshots`.
- Model `players` with minimal roster fields: team reference, full name, position, and shirt number.
- Model `matches` with `city_id`, `home_team_id`, `away_team_id`, `competition`, `stage`, `kickoff_time`, `status`, and `tags`.
- Constrain match status to scheduled, live, completed, postponed, and cancelled.
- Keep match stage as flexible text to avoid over-modeling tournament rules.
- Model `match_stats` as one row per team per match with deterministic numeric fields such as goals, possession, shots, shots on target, passes, corners, and fouls.
- Model `match_events` with structured event type, minute, optional stoppage minute, team, optional player, and description.
- Support minimal event types: goal, yellow card, red card, substitution, and var review.
- Model `tactical_snapshots` as per-team, per-match structured tactical state with snapshot minute, formation, possession style, press intensity, defensive line, and confidence.
- Add required indexes for city, team, match, and kickoff query paths.
- Add composite indexes for common demo reads: matches by city/kickoff and events by match/minute.
- Use idempotent migration constructs: `create table if not exists`, `alter table add column if not exists`, `create index if not exists`, `drop policy if exists`, and `insert ... on conflict`.
- Seed all official World Cup 2026 host cities and all participating countries/teams as reference data.
- Keep player, match, stat, event, and tactical seed data small but realistic, prioritizing Toronto and Vancouver first.
- Enable row level security on public domain tables and create public read policies only.
- Do not allow authenticated or anonymous client writes to sports domain tables.
- Add minimal backend read capability for cities and matches if absent.
- Keep backend route responses aligned with existing API contract DTOs, including pagination and observability metadata where applicable.
- Query Supabase through a narrow backend service interface so domain routes are testable with mocked responses.
- Preserve local-first behavior: missing Supabase configuration should not break health checks or unrelated builds.

## Testing Decisions

- Backend tests should verify external behavior and response contracts for city and match reads using mocked Supabase/domain service responses.
- Tests should cover filtering matches by city, pagination shape, empty result behavior, and observability metadata presence.
- Tests should cover missing Supabase configuration for domain routes as a clear degraded or unavailable response without affecting `/health`.
- Migration validation should be documented and run when Supabase CLI/local Supabase is available.
- Migration checks should confirm that the migration can be applied repeatedly, seed rows upsert cleanly, and required indexes exist.
- RLS behavior should be checked at least manually or through opt-in integration tests if Supabase test credentials are available: public reads succeed and client writes are not permitted.
- Normal test runs must not require hosted Supabase or external sports APIs.

## Out of Scope

- Paid sports data providers.
- Live fixture, score, roster, or event polling.
- Always-on background jobs.
- Full official match schedule ingestion.
- Full player rosters for all teams.
- Real-time match updates.
- AI-generated match facts, tactical claims, or rankings.
- Venue, hotspot, itinerary, recommendation, or fan-density scoring beyond the schema needed to support later work.
- Exact user coordinates, raw check-in data, or internal telemetry exposure.
- Admin UI for editing sports reference data.

## Further Notes

- The ticket path provided in chat was not present in the local checkout, so the conversation ticket content is the source of truth for this PRD.
- FIFA references list 16 host cities across Canada, Mexico, and the United States, and describe the 2026 tournament as a 48-team event.
- The team seed list should be refreshed from an official source immediately before implementation if the repo seed data is stale.
- Existing migration data already includes many host cities and teams; implementation should preserve those IDs where existing application state may reference them.
- Demo fixtures should be realistic but clearly seeded. They should not claim to be live official fixtures unless the implementation deliberately seeds official schedule facts from a vetted static source.
