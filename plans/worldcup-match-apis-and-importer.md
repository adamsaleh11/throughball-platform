# Plan: World Cup Match APIs and Importer

> Source PRD: `docs/prds/worldcup-match-apis-and-importer.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: Keep flat routes: `GET /matches`, `GET /matches/{match_id}`, `GET /matches/{match_id}/stats`, `GET /matches/{match_id}/events`, and `GET /matches/{match_id}/momentum`.
- **Schema**: Use the existing Supabase World Cup tables: `matches`, `match_stats`, `match_events`, `tactical_snapshots`, `teams`, `host_cities`, and `players`.
- **Key models**: Match list/detail, match stats, match events, and match momentum are typed API response contracts with observability metadata.
- **Auth**: These public World Cup reads continue to use public-read RLS and the configured Supabase anon key.
- **External services**: Runtime APIs never call API-Football. API-Football is only used by a manual local importer that reads its key from the environment.
- **Compliance**: Generated provider-derived artifacts stay out of git by default unless licensing is reviewed separately.

---

## Phase 1: Typed Match List Baseline

**User stories**: 1-4, 12-18, 25-26

### What to build

Extend the existing match list endpoint so it returns all matches across all cities by default, supports city/status filtering, preserves pagination metadata, uses typed response models, includes observability metadata, and avoids unnecessary count payloads.

### Acceptance criteria

- [ ] `GET /matches` returns all available matches ordered by kickoff time.
- [ ] `GET /matches?city_id=...` filters to that city.
- [ ] `GET /matches?status=...` filters to that status.
- [ ] Responses include stable typed match and pagination shapes.
- [ ] Responses include request metadata.
- [ ] Tests prove all-cities behavior and seeded Toronto/Vancouver compatibility.

---

## Phase 2: Match Detail and Not Found Contract

**User stories**: 5-6, 12-18, 28

### What to build

Add single-match detail reads that return compact city/team labels and return structured not-found errors when the match does not exist.

### Acceptance criteria

- [ ] `GET /matches/{match_id}` returns compact match detail for an existing match.
- [ ] Missing match IDs return `404`.
- [ ] Success and error responses include observability metadata.
- [ ] Tests cover success, not-found, and storage failure behavior.

---

## Phase 3: Stats, Events, and Momentum Reads

**User stories**: 7-11, 12-18, 27-28, 30

### What to build

Add deterministic subresource endpoints for stats, event timeline, and tactical momentum snapshots using existing Supabase tables and indexed `match_id` access paths.

### Acceptance criteria

- [ ] `GET /matches/{match_id}/stats` returns one stat row per team.
- [ ] `GET /matches/{match_id}/events` returns events in match-clock order.
- [ ] `GET /matches/{match_id}/momentum` returns tactical snapshots.
- [ ] Existing matches with no subresource rows return empty collections.
- [ ] Missing matches return structured `404`.
- [ ] Tests cover success and empty collection behavior.

---

## Phase 4: Manual API-Football Importer

**User stories**: 19-24, 29

### What to build

Add a reusable local importer that fetches API-Football data only when manually run, normalizes provider teams and fixtures into the existing schema, supports inspection before apply, and keeps provider-derived generated artifacts outside git.

### Acceptance criteria

- [ ] Importer requires `API_FOOTBALL_KEY` from the environment.
- [ ] Importer supports dry-run/emit behavior without writing to Supabase.
- [ ] Importer can emit idempotent upsert SQL for teams and matches.
- [ ] Generated provider-derived output is gitignored.
- [ ] Tests use fixture JSON and do not call API-Football.
- [ ] Tests prove secrets are not written to generated output.

---

## Phase 5: End-to-End Acceptance and Operator Docs

**User stories**: 18, 20-28

### What to build

Verify the complete backend behavior and document the operator workflow for refreshing match data without turning provider calls into runtime dependencies.

### Acceptance criteria

- [ ] Relevant backend tests pass.
- [ ] Importer tests pass.
- [ ] Documentation explains how to run the importer with an environment key.
- [ ] Documentation warns that provider-derived output should not be committed without licensing review.
- [ ] Git status shows no committed secrets or provider-derived generated data.
