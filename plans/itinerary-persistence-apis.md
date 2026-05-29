# Plan: Itinerary Persistence APIs

> Source PRD: docs/prds/itinerary-persistence-apis.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: authenticated itinerary APIs use `POST /itineraries/generate`, `POST /itineraries/save`, and `GET /itineraries/me`.
- **Schema**: private saved plans are stored in `itineraries`; ordered child entries are stored in `itinerary_items`.
- **Key models**: an itinerary stores normalized request input, deterministic `input_hash`, title, summary, status, and ordered items with source links and approximate route context.
- **Auth**: all itinerary routes require Supabase bearer auth and pass caller-scoped requests through Supabase so RLS is exercised.
- **External services**: this phase uses Supabase persistence only. `/generate` is a `501` stub; no ADK agent, LLM, RAG, paid routing, or live places APIs are called.
- **Privacy**: itineraries are private user-scoped records. Payloads must not store exact user coordinates, raw check-ins, or internal telemetry.

---

## Phase 1: Authenticated Generate Stub

**User stories**: 9, 10, 14, 15, 16

### What to build

Expose the protected generation route so frontend and later agent work have a stable contract. Authenticated callers receive a structured `501 Not Implemented` response with standard observability metadata; unauthenticated callers receive the standard itinerary unauthorized error.

### Acceptance criteria

- [ ] `POST /itineraries/generate` rejects missing or invalid bearer tokens.
- [ ] Authenticated callers receive HTTP `501`.
- [ ] The `501` response includes a stable itinerary generation error code, message, details, and observability metadata.
- [ ] No generation, LLM, RAG, routing, or external provider call is attempted.

---

## Phase 2: Save And Reuse Itinerary

**User stories**: 1, 3, 4, 5, 6, 7, 11, 13, 17, 18, 19, 20

### What to build

Allow a signed-in user to save a complete itinerary aggregate with normalized input and ordered items. The service computes the input hash, stores the aggregate privately, and returns an existing saved itinerary when the same user submits the same normalized inputs again.

### Acceptance criteria

- [ ] `POST /itineraries/save` rejects missing or invalid bearer tokens.
- [ ] Authenticated users can save an itinerary with ordered items and receive HTTP `201`.
- [ ] The response returns the canonical persisted itinerary aggregate.
- [ ] Repeating the same normalized input for the same user returns the existing itinerary with HTTP `200` and `reused: true`.
- [ ] Input hashes are deterministic across object key order, interest ordering, and omitted optional fields.
- [ ] Saved itinerary payloads do not include exact user coordinates or raw check-in records.
- [ ] Itinerary tables are protected by user-scoped RLS.

---

## Phase 3: Load My Itineraries

**User stories**: 2, 8, 12, 16

### What to build

Expose saved itinerary history for the authenticated user as paginated full aggregates. The endpoint returns newest plans first and includes each itinerary's ordered items so the frontend can render saved trips without a separate detail endpoint in this phase.

### Acceptance criteria

- [ ] `GET /itineraries/me` rejects missing or invalid bearer tokens.
- [ ] Authenticated users receive only their own saved itinerary aggregates.
- [ ] Results are paginated with default page 1, default page size 20, and maximum page size 100.
- [ ] Results are ordered newest first.
- [ ] Each returned itinerary includes ordered items and observability metadata.

---

## Phase 4: Contract Hardening

**User stories**: 14, 15, 16, 17, 18, 19, 21, 22

### What to build

Harden the public contract and operational guarantees around the new APIs. Cover schema contracts, RLS policy expectations, storage error mapping, API documentation, and regression behavior against the existing backend suite.

### Acceptance criteria

- [ ] Migration contract tests prove `itineraries` and `itinerary_items` exist with required indexes and policies.
- [ ] Migration contract tests prove no public itinerary read or write policies exist.
- [ ] Storage failures map to stable structured itinerary errors.
- [ ] API contract documentation includes itinerary request and response shapes.
- [ ] Existing profile, fan, city guide, and World Cup API tests continue to pass.
