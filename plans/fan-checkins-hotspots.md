# Plan: Fan Check-Ins and Hotspots

> Source PRD: docs/prds/fan-checkins-hotspots.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: authenticated fan activity uses `POST /fan/checkins` and `GET /fan/checkins/me`; public aggregate discovery uses `GET /cities/{city_id}/hotspots`.
- **Schema**: private activity is stored in `fan_checkins`, `fan_rsvps`, and `fan_signals`; public aggregate serving data is stored in `fan_hotspots`; aggregate snapshots are stored in `hotspot_history`.
- **Key models**: check-ins are private user-scoped records; hotspots are aggregate city/match records with score, confidence, supporter count, coarse center, and ranking factors.
- **Auth**: check-in routes require bearer auth and pass the caller JWT through to Supabase so RLS is exercised; public hotspots are unauthenticated aggregate reads.
- **External services**: use Supabase REST only. No paid map APIs, realtime streams, background workers, or LLM calls are part of this foundation.
- **Privacy**: exact coordinates may be accepted for private check-ins, but public APIs read only aggregate hotspot tables and never expose individual check-ins.

---

## Phase 1: Private Check-In Contract

**User stories**: 1, 2, 3, 5, 19, 20, 21, 22

### What to build

Create the authenticated check-in path so a signed-in fan can write a private check-in for a host city with optional match and venue context. The API returns a sanitized check-in contract and request metadata while private coordinates remain confined to storage.

### Acceptance criteria

- [ ] `POST /fan/checkins` rejects missing or invalid bearer tokens.
- [ ] Authenticated users can create a private check-in with city and coordinate data.
- [ ] The response includes check-in identifiers and timestamps but does not expose raw latitude or longitude.
- [ ] Private check-in storage is protected by user-scoped RLS policies.
- [ ] API errors include structured error payloads and observability metadata.

---

## Phase 2: My Check-Ins

**User stories**: 4, 5, 6, 19, 20, 22

### What to build

Expose a personal check-in history endpoint that returns only the authenticated user's check-ins in a paginated, sanitized response. The behavior should prove the user-scoped access pattern before broader fan intelligence features build on it.

### Acceptance criteria

- [ ] `GET /fan/checkins/me` rejects missing or invalid bearer tokens.
- [ ] Authenticated users receive only their own check-ins.
- [ ] The response is paginated and ordered for recent activity.
- [ ] The response omits raw latitude and longitude unless explicitly revisited by product.
- [ ] Tests cover the route contract and auth behavior.

---

## Phase 3: Public Seeded Hotspots

**User stories**: 7, 8, 9, 10, 12, 13, 14, 18, 19, 22

### What to build

Serve public city hotspots from aggregate-only seeded data so demos work before live traffic exists. The public API exposes area labels, coarse centers, scores, confidence, supporter counts, ranking factors, pagination, and metadata.

### Acceptance criteria

- [ ] `GET /cities/{city_id}/hotspots` returns aggregate hotspots without authentication.
- [ ] Hotspot responses include score, confidence, supporter count, coarse center, ranking factors, and update time.
- [ ] Seeded aggregate rows exist for demo-ready host cities.
- [ ] Public hotspot responses never include user IDs, check-in IDs, raw latitude, raw longitude, or individual check-in timestamps.
- [ ] The public endpoint reads from aggregate hotspot storage only.

---

## Phase 4: Fan Intelligence Foundations

**User stories**: 15, 16, 17, 21

### What to build

Establish the persistence foundations for future fan intelligence inputs and trends. RSVP and signal tables exist with safe policies, and hotspot history records aggregate snapshots rather than individual events.

### Acceptance criteria

- [ ] `fan_rsvps` exists with user-scoped RLS policies.
- [ ] `fan_signals` exists with user-scoped RLS policies for user-originated signals.
- [ ] `hotspot_history` stores aggregate hotspot snapshots.
- [ ] Client write policies are not granted for public aggregate hotspot tables.
- [ ] The schema supports later manual aggregation without introducing workers in this slice.

---

## Phase 5: Scoring, Confidence, and Filtering Polish

**User stories**: 10, 11, 12, 17, 18, 20, 22

### What to build

Tighten deterministic public hotspot behavior: support match filtering, keep small payloads through pagination, model confidence separately from score, and enforce aggregate privacy thresholds for live-derived data.

### Acceptance criteria

- [ ] Public hotspots can be filtered by `match_id`.
- [ ] Pagination parameters constrain response size.
- [ ] Score is represented as a deterministic `0..100` ranking value.
- [ ] Confidence is represented as a deterministic `0..1` reliability value.
- [ ] Live-derived aggregate rows below the minimum supporter threshold are not publishable.
