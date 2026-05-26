## Problem Statement

Fans need a way to privately check in around World Cup host cities so the product can surface where supporter activity is building without exposing individual movement. Today the platform has seeded host city and match data, authenticated profile persistence, and public catalog APIs, but it does not yet have a fan intelligence foundation for check-ins, RSVPs, signals, or aggregate hotspots.

The immediate need is a backend slice that lets authenticated users create and view their own check-ins while giving public clients aggregate hotspot data suitable for demos and future recommendation flows. The system must protect exact user coordinates and raw check-in records, keep backend costs low, and preserve the repo's deterministic-first architecture.

## Solution

Build a private fan check-in and public hotspot backend foundation. Authenticated users can create private check-ins and fetch their own check-in history. Public clients can fetch aggregate hotspots for a city through a city-scoped endpoint that reads only aggregate tables.

The backend will use Supabase as the only persistence service. Private tables will be protected by row-level security so users can only access their own records. Public hotspot APIs will serve from aggregate hotspot tables, not from raw check-ins. Seeded aggregate hotspots will provide realistic demo data before live traffic exists.

Hotspots will expose deterministic score and confidence values. Score ranks activity or usefulness, while confidence describes reliability based on aggregate volume, recency, and source diversity. No paid map APIs, realtime streaming, background workers, or LLM calls are part of this slice.

## User Stories

1. As an authenticated fan, I want to create a private check-in for a host city, so that my activity can contribute to aggregate fan intelligence.
2. As an authenticated fan, I want my check-in to optionally include match and venue context, so that future recommendations can understand why I checked in.
3. As an authenticated fan, I want exact coordinates treated as private data, so that my precise location is not exposed publicly.
4. As an authenticated fan, I want to see my own check-ins, so that I can review my activity.
5. As an authenticated fan, I want check-in APIs to reject missing or invalid bearer tokens, so that other users cannot write or read my activity.
6. As an authenticated fan, I want only my own check-ins returned from the "my check-ins" endpoint, so that user activity remains isolated.
7. As a public user, I want to fetch hotspots for a city, so that I can discover areas with strong supporter activity.
8. As a public user, I want hotspot responses to include area labels and coarse centers, so that I can understand approximate fan activity without exposing individuals.
9. As a public user, I want hotspots to include a score, so that I can compare which areas are most active or relevant.
10. As a public user, I want hotspots to include a confidence value, so that I can distinguish strong aggregate intelligence from lower-confidence seeded or sparse data.
11. As a public user, I want hotspot responses to support optional match filtering, so that I can view activity related to a specific match when available.
12. As a public user, I want hotspot responses to be paginated or limited, so that clients receive small, predictable payloads.
13. As a privacy-conscious fan, I want public hotspot APIs to never expose user IDs, check-in IDs, exact coordinates, raw timestamps, or individual check-in rows, so that aggregate intelligence cannot be reverse engineered into personal activity.
14. As a demo operator, I want seeded aggregate hotspots for host cities, so that demos work before organic check-in traffic exists.
15. As a backend developer, I want fan RSVP and fan signal tables established now, so that later scoring work has stable persistence foundations.
16. As a backend developer, I want hotspot history stored as aggregate snapshots, so that trends can be computed later without storing public individual events.
17. As a backend developer, I want manual aggregation to be possible in development, so that hotspot data can be refreshed without a background worker.
18. As a backend developer, I want the public hotspot endpoint to read only aggregate tables, so that privacy is enforced by architecture and not just response filtering.
19. As an operator, I want every new API response to include request metadata, so that request tracing, latency, retries, and degraded execution remain observable.
20. As an operator, I want storage failures returned as structured API errors, so that clients receive predictable failure responses.
21. As a security reviewer, I want RLS policies on all private fan tables, so that Supabase prevents cross-user data access even if application code is wrong.
22. As a tester, I want behavioral tests around auth, check-in privacy, hotspot contracts, and aggregate-only public output, so that regressions are caught at the API boundary.

## Implementation Decisions

- Build a fan backend module that follows the existing route and core service/store pattern used by profile and World Cup catalog APIs.
- Add the public route `GET /cities/{city_id}/hotspots`.
- Add the authenticated routes `POST /fan/checkins` and `GET /fan/checkins/me`.
- Require bearer authentication for check-in creation and personal check-in reads.
- Keep public hotspot reads unauthenticated.
- Use Supabase REST queries only. Authenticated endpoints pass the caller's user token so RLS is exercised. Public aggregate reads use the anon key.
- Add Supabase tables for `fan_checkins`, `fan_rsvps`, `fan_signals`, `fan_hotspots`, and `hotspot_history`.
- Store exact latitude and longitude only in private check-in rows. Public hotspot responses use coarse aggregate center fields and an explicit precision label.
- Allow check-ins to reference `city_id`, optional `match_id`, and optional `venue_id` when those IDs are available.
- Treat check-in visibility as private for this slice. If a visibility field is accepted or stored, only private behavior is supported.
- Serve public hotspots from `fan_hotspots`; do not query `fan_checkins` from the public endpoint.
- Use `hotspot_history` for aggregate snapshots, not individual activity.
- Seed realistic aggregate hotspots for demo-ready host cities without requiring live check-in traffic.
- Keep `fan_rsvps` and `fan_signals` as persistence foundations in this slice. Public API support for RSVP and signal writes is out of scope unless a later ticket adds it.
- Model hotspot `score` as a deterministic `0..100` ranking value.
- Model hotspot `confidence` as a deterministic `0..1` reliability value.
- Confidence should account for aggregate volume, recency, and source diversity when live data exists, while seeded rows can carry explicit confidence suitable for demos.
- Suppress or avoid publishing live-derived hotspots below a minimum aggregate threshold of three supporters.
- Include response metadata with `request_id`, `trace_id`, `latency_ms`, `retries`, and `degraded` on all new endpoints.
- Preserve low-cost operation: no paid map APIs, no realtime check-in stream, no background workers, and no LLM calls.

## Testing Decisions

- Test API behavior at the route contract boundary rather than internal implementation details.
- Add tests proving unauthenticated users cannot create check-ins or read personal check-in history.
- Add tests proving authenticated check-in creation returns a sanitized private contract.
- Add tests proving personal check-in history is scoped to the current user through the service contract.
- Add tests proving public hotspot responses include aggregate hotspot fields and response metadata.
- Add privacy regression tests proving public hotspot payloads do not include `user_id`, `checkin_id`, raw `latitude`, raw `longitude`, or individual check-in timestamps.
- Add tests for optional hotspot filtering by `match_id` and pagination or limit behavior.
- Add migration review coverage for table creation, RLS enablement, public-read aggregate policies, and private user-scoped policies.
- Follow existing FastAPI `TestClient` and dependency override patterns used by profile and World Cup API tests.
- Keep Supabase-backed RLS integration tests optional and skipped unless real test environment variables are present.

## Out of Scope

- Frontend check-in UI.
- Venue discovery or paid map API integration.
- Realtime check-in streaming.
- Automatic background aggregation workers.
- Public endpoints for fan RSVPs or fan signals.
- AI summaries, AI ranking, or LLM-generated hotspot explanations.
- Recommendation or itinerary APIs.
- Exact geocoding, reverse geocoding, or map tile work.
- Administrative moderation tools.
- Push notifications or alerting when hotspots change.

## Further Notes

- The ticket path referenced in the request is not present in the checkout, so the provided ticket text is the source of truth.
- Older API contract documentation mentions `/check-ins`, `/check-ins/aggregates`, and `/hotspots`; this PRD intentionally follows the newer ticket paths unless compatibility is later requested.
- The first implementation should favor stable contracts and privacy boundaries over sophisticated aggregation.
- Seeded demo data should be clearly aggregate-only and should not require fake user check-ins.
- Future work can add explicit aggregation commands, RSVP APIs, signal ingestion APIs, venue-aware scoring, and trend endpoints once this foundation is in place.
