# World Cup Match APIs and Importer PRD

## Problem Statement

Throughball has a World Cup core schema in Supabase, but the backend only exposes a small city/match catalog surface. The product now needs typed match APIs for list, detail, stats, events, and momentum so frontend and demo flows can read deterministic football data without live provider calls or AI-generated facts.

The current seeded data is useful for Toronto and Vancouver demos, but it is not enough as the app moves toward all host cities and more realistic World Cup coverage. Operators also need a repeatable way to refresh local Supabase data from a sports data provider while keeping runtime APIs low-cost, index-backed, and independent of external services.

This matters now because later fan heatmap, venue, itinerary, and recommendation work depends on stable match identifiers, kickoff ordering, team labels, match timelines, and tactical context. The backend should query and shape known data; it should not call an LLM or a live sports API during user requests.

## Solution

Build the requested match API surface over the existing World Cup tables and extend the backend World Cup service boundary to support match detail, stats, events, and momentum reads. The APIs will use flat routes, return typed response contracts, include observability metadata, and rely only on indexed Supabase queries.

Add a reusable local importer script for API-Football. The importer will be an operator-controlled tool, not runtime application code. It will fetch provider data only when manually run, normalize it into the existing Supabase schema, and either apply upserts to Supabase or emit a generated SQL seed artifact that is excluded from git by default. This preserves the runtime cost rule while giving the team a practical path to refresh match data.

The runtime API must continue to work from Supabase only. No external match API calls, websocket streams, polling jobs, or background sync workers are part of request handling.

## User Stories

1. As a frontend user, I want to list World Cup matches across all host cities, so that the app is not limited to Toronto and Vancouver.
2. As a frontend user, I want to filter matches by host city, so that city-specific flows can show only relevant matches.
3. As a frontend user, I want matches ordered by kickoff time, so that schedules appear in a natural chronological order.
4. As a frontend user, I want match rows to include team names, kickoff time, status, competition, and tags, so that match selectors are readable.
5. As a frontend user, I want to open a single match detail, so that the app can render a focused match view.
6. As a frontend user, I want missing matches to return a clear not-found response, so that the app can show an appropriate empty/error state.
7. As a frontend user, I want match stats by team, so that the UI can compare goals, possession, shots, passing, corners, and fouls.
8. As a frontend user, I want match events in match-clock order, so that the UI can render a deterministic timeline.
9. As a frontend user, I want events to include compact team and player labels when available, so that timelines do not display raw IDs.
10. As a frontend user, I want match momentum data, so that the UI can show tactical state without inventing analysis.
11. As a frontend user, I want matches with no snapshots to return an empty momentum list, so that absence of tactical data is handled gracefully.
12. As an API consumer, I want all match APIs to include request metadata, so that calls are traceable during development and demos.
13. As an API consumer, I want typed response contracts, so that frontend clients can rely on stable payload shapes.
14. As a backend developer, I want match APIs backed by the existing World Cup service interface, so that tests can mock the domain boundary cleanly.
15. As a backend developer, I want Supabase queries to select only needed columns, so that payloads stay small.
16. As a backend developer, I want match list queries to use kickoff and city indexes, so that schedule reads stay low-latency.
17. As a backend developer, I want detail, stats, events, and momentum reads to start from `match_id`, so that they use existing indexed access paths.
18. As an operator, I want request completion logs to include `request_id`, so that API behavior can be correlated across logs and responses.
19. As an operator, I want runtime match APIs to avoid external sports providers, so that provider downtime and quota limits do not break the app.
20. As an operator, I want a manual importer script for API-Football, so that I can refresh Supabase match data when I choose.
21. As an operator, I want the importer to require an environment variable for the provider key, so that secrets are not written into the repo.
22. As an operator, I want the importer to log counts and errors without logging secrets, so that refreshes are auditable but safe.
23. As an operator, I want imported provider data kept out of committed migrations by default, so that the repo does not redistribute a third-party sports dataset.
24. As an operator, I want the importer to be idempotent, so that rerunning it updates the same logical teams and matches instead of duplicating rows.
25. As a tester, I want API tests to cover the seeded Toronto and Vancouver match data path, so that demo acceptance stays intact.
26. As a tester, I want tests to cover all-cities match listing, so that the implementation does not accidentally special-case Canadian demo matches.
27. As a tester, I want tests to cover empty stats, events, and momentum collections, so that incomplete provider data does not break clients.
28. As a tester, I want tests to cover storage failures, so that Supabase outages produce structured errors with metadata.
29. As a maintainer, I want provider-specific normalization hidden behind a script-level module boundary, so that changing providers later does not affect runtime APIs.
30. As a maintainer, I want no AI synthesis in this match data path, so that facts, ordering, and stats remain deterministic.

## Implementation Decisions

- Keep the flat route namespace requested by the ticket: `GET /matches`, `GET /matches/{match_id}`, `GET /matches/{match_id}/stats`, `GET /matches/{match_id}/events`, and `GET /matches/{match_id}/momentum`.
- Preserve the existing `GET /matches` behavior and extend it rather than introducing a parallel World Cup router prefix.
- `GET /matches` returns all matches across all cities by default, ordered by kickoff time.
- `GET /matches` supports optional `city_id`, `status`, `page`, and `page_size` parameters.
- `page_size` remains bounded to keep payloads small.
- Match list responses keep pagination metadata with page, page size, total items, total pages, and next-page state.
- Match detail responses return compact match data and enough city/team labels for a readable detail view.
- Match detail does not embed stats, events, or momentum; those remain separate small endpoints.
- Missing match detail returns a structured `404` error with observability metadata.
- Stats responses return one row per team per match with numeric fields already represented in the core schema.
- Events responses return match events ordered by match clock and include compact team/player labels when available.
- Momentum responses are backed by `tactical_snapshots`. The endpoint returns deterministic tactical snapshots, not AI-generated momentum.
- A match with no tactical snapshots returns an empty momentum collection rather than a `404`.
- Runtime APIs query Supabase only. They do not call API-Football or any other sports provider.
- Runtime APIs use the existing Supabase REST approach and public-read RLS policies.
- Runtime queries should select only needed fields and rely on existing indexes on match ID, kickoff time, city, and event minute.
- The current list-count implementation should be improved so count metadata does not require fetching all IDs when Supabase count headers can provide the value.
- Add explicit typed response models for match list, detail, stats, events, momentum, and error responses.
- Continue using the existing observability middleware for request completion logs, headers, latency, retries, and degraded state.
- Ensure every new route includes response metadata matching existing API conventions.
- Add a local importer script for API-Football.
- The importer must read the provider key from an environment variable, not from committed config.
- The importer must not log the provider key or write it to generated files.
- The importer must support a dry-run or emit-only mode so operators can inspect the normalized output before applying it.
- The importer should support an apply mode for updating Supabase when Supabase credentials are available.
- Generated provider-derived SQL or JSON artifacts should be excluded from git by default.
- Provider-derived data should not be committed as a static migration unless the team has confirmed licensing and redistribution rights.
- The importer maps provider teams and fixtures into existing `teams` and `matches` records and preserves existing seeded IDs where practical.
- The importer may leave stats, events, players, and tactical snapshots empty when the provider response lacks reliable data for those surfaces.
- No background sync, cron job, websocket stream, or hosted worker is introduced in this PRD.
- No logos, player photos, or branded provider assets are imported by default.
- API-Football usage remains subject to provider plan limits and terms; the importer is an operator convenience, not a guarantee of complete official data.

## Testing Decisions

- API tests should verify external response contracts rather than implementation internals.
- Tests should cover all five requested match route families.
- Tests should verify `GET /matches` returns all matches by default and can filter by city.
- Tests should verify match list ordering by kickoff time.
- Tests should verify pagination shape and bounded page size behavior.
- Tests should verify match detail success and missing-match `404` behavior.
- Tests should verify stats, events, and momentum success payloads.
- Tests should verify empty stats/events/momentum collections are represented consistently when the match exists.
- Tests should verify structured storage errors include response metadata.
- Tests should verify response metadata includes `request_id`, `trace_id`, latency, retries, and degraded state.
- Service-layer tests should verify mapping from Supabase rows into typed match, stat, event, and momentum contracts.
- Store/query tests should verify the Supabase query builder uses indexed filters and small column selections where practical.
- Importer tests should use fixture JSON and validate normalization into schema-shaped records without calling API-Football.
- Importer tests should verify missing API keys fail clearly.
- Importer tests should verify secrets are not included in generated output.
- Importer tests should verify idempotent upsert output for teams and matches.
- Normal test runs must not require a live Supabase instance or API-Football network access.

## Out of Scope

- Runtime calls to API-Football or any external match provider.
- Background sync, cron refresh, polling workers, or websocket/live-score streaming.
- AI-generated match facts, rankings, event summaries, tactical claims, or momentum.
- Full official roster import for all teams unless the provider data is available and explicitly needed later.
- Importing logos, photos, federation marks, or other visual assets from the provider.
- Public redistribution of provider-derived datasets as committed migrations without a licensing review.
- Admin UI for editing imported match data.
- Frontend match detail screens.
- Venue, hotspot, itinerary, recommendation, or fan-density scoring.
- Exact user coordinates, raw check-in data, or internal telemetry exposure.
- Replacing the existing World Cup core schema.

## Further Notes

- The ticket path in the original prompt is not present in the checkout; the pasted ticket content is the source for this PRD.
- The existing World Cup migration already creates the required core tables and indexes and seeds Toronto/Vancouver demo data.
- The existing backend route already exposes `GET /matches`; implementation should preserve its external compatibility while broadening coverage.
- The user confirmed that match listing should be for all cities, not only Toronto/Vancouver.
- The user requested a reusable script that can be run manually to update the table from API-Football.
- The provider API key was shared in chat and should be rotated after use. It must not be committed.
- API-Football/API-Sports terms allow building applications with their data but restrict resale and may not grant full publication rights for third-party sports data; generated provider-derived artifacts should stay local by default.
- The repo had very little free disk space during PRD creation; generated frontend build cache was cleared to allow writing project artifacts.
