## Problem Statement

Throughball has deterministic host city, match, fan hotspot, and city guide data foundations, but it does not yet have a way to persist itinerary outputs for authenticated users. The future ADK itinerary agent will be costly enough that the platform should not regenerate the same itinerary repeatedly for the same user and the same inputs. Fans also need saved itineraries to be available later across sessions rather than existing only as transient frontend or agent output.

This matters now because the itinerary API contract must be stable before Phase 06 wires in the ADK agent. The backend needs to establish private user-scoped persistence, duplicate prevention by input hash, and a contract-shaped `/generate` stub that frontend work can build against without implying that itinerary generation is already available.

## Solution

Build authenticated itinerary persistence APIs backed by Supabase. The backend will let a signed-in user save a complete itinerary payload, fetch their saved itineraries later, and avoid duplicate saves for the same normalized request inputs. The `/generate` endpoint will exist but return a clear `501 Not Implemented` response until Phase 06 connects the ADK itinerary agent.

The system will store the original normalized request input separately from the itinerary output. It will compute a deterministic input hash from the normalized input and scope duplicate prevention to the authenticated user. If the same user submits the same inputs again, the API returns the existing itinerary rather than creating another row.

Itinerary generation is not part of this phase. When generation is implemented later, candidates should come from structured Supabase data such as host cities, matches, venues, city events, tourist spots, transport hubs, and aggregate hotspot intelligence. RAG may support explanation later, but structured Supabase records remain the source of truth. Runtime APIs in this phase must not call paid routing APIs, live places APIs, scraped event sites, or LLM services.

## User Stories

1. As an authenticated fan, I want to save an itinerary, so that I can return to it later.
2. As an authenticated fan, I want to load my saved itineraries, so that my trip planning survives page refreshes and later sessions.
3. As an authenticated fan, I want itinerary items to remain ordered, so that the itinerary can be displayed as a coherent sequence.
4. As an authenticated fan, I want saved itinerary items to include labels, descriptions, time windows, and approximate route context, so that the frontend can render useful trip details.
5. As an authenticated fan, I want itinerary items to reference seeded platform records where available, so that saved trips can remain connected to venues, events, tourist spots, and transport hubs.
6. As an authenticated fan, I want the same itinerary inputs to reuse an existing saved itinerary, so that I do not cause repeated generation or duplicate saved plans.
7. As an authenticated fan, I want duplicate saves to return the existing itinerary, so that the frontend can treat repeated submissions idempotently.
8. As an authenticated fan, I want only my own saved itineraries returned, so that other users cannot see my trip plans.
9. As an unauthenticated user, I want protected itinerary endpoints to return a clear unauthorized error, so that the frontend can route me to sign in.
10. As a frontend developer, I want `/itineraries/generate` to exist with a stable `501` error body, so that I can stub generation flows before Phase 06.
11. As a frontend developer, I want `/itineraries/save` to return the canonical persisted itinerary aggregate, so that local UI state can be hydrated from server state.
12. As a frontend developer, I want `/itineraries/me` to return paginated full itinerary aggregates, so that I can render saved itineraries without extra detail calls in this phase.
13. As a backend developer, I want input hashing to be deterministic across JSON key order and harmless formatting differences, so that duplicate prevention is reliable.
14. As a backend developer, I want itinerary persistence to use caller-scoped Supabase access, so that RLS is exercised in normal API paths.
15. As a backend developer, I want itinerary APIs to follow existing FastAPI route, service, store, and dependency override patterns, so that the implementation stays consistent with profile and fan APIs.
16. As a backend developer, I want all success and error responses to include observability metadata, so that API behavior is traceable.
17. As an operator, I want private itinerary tables protected by user-scoped RLS, so that user travel plans are not publicly readable.
18. As an operator, I want itinerary storage failures to return structured errors, so that clients can recover predictably.
19. As an operator, I want the system to avoid exact user coordinates and raw check-in records in itinerary payloads, so that privacy boundaries remain intact.
20. As an AI integration developer, I want saved itineraries to include the original request input and source-linked items, so that Phase 06 can reuse deterministic candidates and avoid repeated AI calls.
21. As an AI integration developer, I want RAG to be optional explanatory context rather than the itinerary source of truth, so that the platform stays deterministic-first.
22. As a tester, I want contract tests for schema, RLS, duplicate handling, and route responses, so that persistence behavior is stable before generation is implemented.

## Implementation Decisions

- Add authenticated APIs at `POST /itineraries/generate`, `GET /itineraries/me`, and `POST /itineraries/save`.
- All itinerary APIs require Supabase bearer authentication, including the `/generate` stub.
- `/generate` returns `501 Not Implemented` for authenticated callers until Phase 06.
- `/generate` returns a structured error code indicating itinerary generation is not implemented, plus standard observability metadata.
- `/save` accepts a payload containing request `input` and an `itinerary` aggregate.
- `/save` persists the normalized request input, deterministic input hash, itinerary title, itinerary summary, and ordered itinerary items.
- `/save` returns `201 Created` with the saved aggregate when a new itinerary is created.
- `/save` returns `200 OK` with the existing aggregate and a reused indicator when the authenticated user submits duplicate normalized inputs.
- `GET /itineraries/me` returns the authenticated user's saved itineraries as paginated full aggregates.
- Saved itinerary list ordering is newest first by update and creation time.
- Pagination uses page 1 by default, page size 20 by default, and maximum page size 100.
- The canonical request input includes city ID, optional match ID, optional date, party size, interests, and pace.
- The canonical itinerary output includes title, optional summary, and ordered items.
- Itinerary items include position, item type, optional source table, optional source ID, title, optional description, optional start and end timestamps, optional area label, and approximate route context.
- Allowed source table values are limited to structured platform records such as venues, city events, tourist spots, and transport hubs.
- Itinerary item source references are stored as source table plus source ID rather than polymorphic foreign keys.
- This phase validates source table names and UUID shapes but does not require cross-table existence checks for every source ID.
- Approximate route context may include labels, modes, and estimated minutes, but must not depend on live paid routing APIs.
- Exact user coordinates, raw check-in rows, internal telemetry, and private fan activity must not be stored inside itinerary payloads.
- Input hashing is scoped by authenticated user and normalized request input.
- Input hashing uses deterministic JSON normalization so semantically identical inputs produce the same hash.
- Interest arrays are normalized for hashing by trimming, deduplicating, and sorting values.
- Optional input fields are normalized to explicit nulls for hashing.
- Add `itineraries` and `itinerary_items` persistence tables.
- The itinerary table stores user ownership, city and optional match references, input hash, input payload, title, summary, status, and timestamps.
- The itinerary item table stores ordered child records with route context as structured JSON.
- Enforce uniqueness on user ID plus input hash.
- Enable RLS on itinerary tables.
- Users can read, insert, update, and delete only their own itinerary rows.
- Users can access itinerary items only through itinerary rows they own.
- No public read policies are added for itinerary persistence tables.
- Runtime persistence uses Supabase REST with the caller JWT so RLS is exercised.
- The implementation should follow existing backend patterns for route modules, core service/store boundaries, auth dependency resolution, storage errors, and route-level dependency overrides.
- The API contract documentation should be updated with the itinerary request and response shapes.

## Testing Decisions

- Test external API behavior and persistence contracts rather than private implementation details.
- Add route tests proving missing bearer auth is rejected for all itinerary endpoints.
- Add route tests proving authenticated `/itineraries/generate` returns the expected `501` error contract.
- Add route tests proving `/itineraries/save` creates an itinerary aggregate and returns `201 Created`.
- Add route tests proving duplicate `/itineraries/save` calls return the existing itinerary with a reused indicator and `200 OK`.
- Add route tests proving `/itineraries/me` returns only authenticated-user aggregates in paginated form.
- Add route tests proving success and error responses include request ID, trace ID, latency, retries, and degraded metadata.
- Add service tests proving input hash normalization is deterministic across JSON key order, interest ordering, and omitted optional fields.
- Add service tests proving duplicate lookup happens before creating a new itinerary.
- Add service tests proving itinerary item ordering is preserved.
- Add storage/error mapping tests proving Supabase failures return stable structured API errors.
- Add migration contract tests proving `itineraries` and `itinerary_items` exist.
- Add migration contract tests proving user-scoped uniqueness on input hash exists.
- Add migration contract tests proving RLS is enabled and user ownership policies exist.
- Add migration contract tests proving no public read or write policies are granted for itinerary tables.
- Keep Supabase integration tests optional and environment-gated if real Supabase RLS validation is added.
- Run the existing API test suite to ensure profile, fan, city guide, and World Cup APIs remain compatible.

## Out of Scope

- Real itinerary generation.
- ADK agent integration.
- LLM calls.
- RAG ingestion or retrieval implementation.
- AI-generated ranking, filtering, or candidate selection.
- Runtime calls to Google Places, paid routing APIs, paid map APIs, live event providers, or scraped event sites.
- Frontend itinerary UI.
- Admin itinerary management UI.
- Sharing itineraries between users.
- Collaborative itinerary editing.
- Deleting or renaming itineraries unless needed by future product work.
- Validating every source ID against every possible source table.
- Live route optimization.
- Exact user coordinate storage.
- Raw check-in exposure.

## Further Notes

- The key product boundary is that this phase stores and retrieves itinerary aggregates; it does not decide which places belong in an itinerary.
- Phase 06 should generate candidate itineraries from structured Supabase records first, then optionally use RAG or agent synthesis only to explain or format the selected records.
- The `/generate` stub should be treated as part of the contract, not as a placeholder route that can return arbitrary framework errors.
- Duplicate prevention is a cost-control mechanism for future generation and should be implemented now even though generation itself is not wired yet.
- Sparse source-linked itinerary records are preferable to invented places or unsupported route claims.
