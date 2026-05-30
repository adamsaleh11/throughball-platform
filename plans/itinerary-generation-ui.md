# Plan: Itinerary Generation UI

> Source PRD: docs/prds/itinerary-generation-ui.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: the itinerary workspace lives at `/app/itineraries`; the protected app dashboard links to it.
- **Schema**: no frontend-driven schema changes. The UI consumes existing persisted itinerary aggregates from the Phase 01 API contract.
- **Key models**: `ItineraryInput`, `Itinerary`, `ItineraryItem`, `GenerateItineraryStubResponse`, and `MyItinerariesResponse`.
- **Auth**: the page follows existing protected app behavior. Configured Supabase environments require a session; local development without Supabase configuration remains viewable.
- **External services**: no AI, RAG, live places API, paid routing API, third-party geocoding, or interactive map provider is used in this phase.
- **Generation boundary**: `POST /itineraries/generate` is called only after explicit user action and currently renders the structured Phase 06 `501` response.
- **Duplicate prevention**: client-side normalization blocks redundant generation attempts for identical form inputs and complements server-side input hash reuse.
- **Sharing**: share behavior is private app-link sharing through a selected itinerary query parameter, not public itinerary access.

---

## Phase 1: Workspace Scaffold + API Contracts

**User stories**: 1-5, 11, 12, 18, 23, 24, 33, 36, 37

### What to build

Add the protected itinerary workspace and dashboard entry. Create typed itinerary API access for generating and loading saved itineraries. The page should load saved itinerary history, handle local-dev auth behavior, and render loading, empty, error, and success states without any generation call on page load.

### Acceptance criteria

- [ ] `/app/itineraries` renders inside the protected app workspace.
- [ ] `/app` exposes a clear navigation entry to `/app/itineraries`.
- [ ] Saved itinerary history loads from the authenticated history endpoint.
- [ ] The saved-history panel has loading, empty, error-with-retry, and success states.
- [ ] Opening the page does not call the generation endpoint.
- [ ] Itinerary API client functions expose typed generation and history contracts.
- [ ] Data fetching uses React Query with no polling and no automatic window-focus refetch.

---

## Phase 2: Structured Generation Form + Stub Response

**User stories**: 5-14, 32

### What to build

Build the itinerary input form using host city data, optional city-filtered match selection, date, party size, fixed interests, and pace controls. Generate is an explicit submit action that calls the real generation endpoint and renders the current structured Phase 06 unavailable response without fabricating itinerary items.

### Acceptance criteria

- [ ] City, optional match, date, party size, interests, and pace inputs map to the itinerary input contract.
- [ ] Matches are loaded for the selected city and the match input remains optional.
- [ ] Generate is disabled until required form values are valid.
- [ ] Clicking Generate calls `POST /itineraries/generate` with the normalized form input.
- [ ] The structured generation-unavailable response is displayed as a staged integration state.
- [ ] The UI does not invent generated itinerary items.
- [ ] No AI or external provider call is made.

---

## Phase 3: Client Duplicate Prevention + Saved Reuse Detection

**User stories**: 15-17, 34, 35

### What to build

Add deterministic input normalization helpers. Use them to prevent duplicate generation attempts for identical current-session inputs and to detect saved itineraries whose persisted input matches the current form.

### Acceptance criteria

- [ ] Interest order, duplicate interests, and whitespace normalize to the same client input key.
- [ ] Duplicate Generate clicks for the same input are blocked while the request is pending.
- [ ] Repeat Generate for the same input is blocked after the generation-unavailable response.
- [ ] A saved itinerary with matching normalized input is highlighted.
- [ ] The UI guides the user to inspect the matching saved itinerary rather than regenerating.
- [ ] Server-side input hash remains the authoritative durable dedupe mechanism.

---

## Phase 4: Saved Itinerary Detail Display

**User stories**: 19-26

### What to build

Let users select a saved itinerary from history and inspect the full persisted aggregate inline. The detail view should show title, summary, input metadata, ordered itinerary items, source references, item timing, area labels, descriptions, and route context.

### Acceptance criteria

- [ ] Saved itinerary cards show title, city, date, party size, pace, item count, and updated time.
- [ ] Selecting a saved itinerary renders its detail panel.
- [ ] Ordered itinerary items render in persisted order.
- [ ] Item detail includes source type, source ID when present, area, times, description, and route context.
- [ ] Existing persisted itineraries show as saved; no fake save flow appears while generation is unavailable.
- [ ] Empty item lists render an honest empty state.

---

## Phase 5: Private Share Link + Map Placeholder

**User stories**: 27-31

### What to build

Add private app-link sharing for the selected itinerary and query-string selection restore. Add a map/routing placeholder that presents selected itinerary areas and approximate route context without loading a map provider or route service.

### Acceptance criteria

- [ ] Share copies `/app/itineraries?itinerary=<id>` for the selected saved itinerary.
- [ ] Opening a URL with a selected itinerary query focuses that itinerary when it exists in history.
- [ ] Stale or unavailable selected itinerary query values fall back gracefully.
- [ ] The map placeholder renders selected itinerary areas and route context when available.
- [ ] The map placeholder has a clear empty state when no itinerary is selected.
- [ ] No paid routing, map, geocoding, or external provider request is made.

---

## Phase 6: Verification + Polish Pass

**User stories**: all, especially 3, 4, 23, 24, 31, 32, 36

### What to build

Finish responsive layout, accessibility, state handling, and visual polish. Verify the feature through focused API/helper/component tests, typecheck, lint, and a local browser inspection.

### Acceptance criteria

- [ ] Focused itinerary API, helper, and component tests pass.
- [ ] Existing relevant frontend tests continue to pass.
- [ ] Typecheck passes.
- [ ] Lint passes.
- [ ] Browser inspection confirms the page is usable at desktop and mobile widths.
- [ ] The final UI matches the existing protected app style and avoids marketing-page treatment.
