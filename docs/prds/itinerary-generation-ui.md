## Problem Statement

Throughball has authenticated itinerary persistence APIs that can save, deduplicate, and load itinerary aggregates, but the web app does not yet expose a user-facing itinerary workspace. Fans cannot submit itinerary inputs, inspect saved plans, or understand how the Phase 06 generator will fit into the existing deterministic platform.

This matters now because Phase 05 needs a low-cost frontend surface over the Phase 01 persistence contract before real generation is implemented. The UI must prove the form, history, duplicate-prevention, saved itinerary display, and share placeholder flows without inventing itinerary content, calling paid routing services, or auto-triggering generation on page load.

## Solution

Build a protected itinerary workspace in the app. The page lets a signed-in user enter itinerary inputs, explicitly click Generate, see the current Phase 06 `501 Not Implemented` generation response, load saved itineraries, select a saved itinerary for detailed display, copy a private app URL for the selected itinerary, and view a map/routing placeholder.

The page uses the existing itinerary persistence API contracts. Saved itineraries load from the authenticated history endpoint and render their canonical persisted title, summary, input, ordered items, source references, timing, area labels, and approximate route context. The form never auto-generates on page load. The client also prevents duplicate generation attempts for identical normalized inputs during the current page session and points users toward a matching saved itinerary when one exists.

## User Stories

1. As an authenticated fan, I want to open an itinerary workspace from the protected app dashboard, so that I can plan around a host city without leaving Throughball.
2. As an authenticated fan, I want itinerary planning to live at a stable app route, so that I can return to the workspace directly.
3. As a local developer, I want the itinerary workspace to remain usable when Supabase frontend configuration is absent, so that frontend development stays local-first.
4. As an unauthenticated visitor in a configured Supabase environment, I want protected itinerary routes to redirect to login, so that private itinerary data is not exposed.
5. As a fan, I want a city selector sourced from supported host cities, so that itinerary inputs stay aligned with deterministic platform data.
6. As a fan, I want an optional match selector filtered by city, so that I can tie a plan to a match when relevant.
7. As a fan, I want to submit an itinerary date, so that the future generator receives the intended planning day.
8. As a fan, I want to set party size within supported limits, so that the itinerary request matches the backend contract.
9. As a fan, I want to select interests from fixed options, so that the request stays structured and does not become prompt-like free text.
10. As a fan, I want to choose a pace, so that the future generator can distinguish relaxed, balanced, and packed plans.
11. As a fan, I want the page to make no generation request until I click Generate, so that opening the page has no unnecessary generation cost.
12. As a fan, I want the Generate button to call the real generation endpoint, so that the frontend proves the Phase 01 API contract even before generation is implemented.
13. As a fan, I want the current Phase 06-not-ready response shown clearly, so that I understand generation is staged rather than broken.
14. As a fan, I want the UI to avoid fake generated itinerary items, so that Throughball does not present invented recommendations as persisted facts.
15. As a fan, I want repeated clicks for identical inputs to be blocked while a request is pending, so that I do not accidentally submit duplicate generation attempts.
16. As a fan, I want repeated generation attempts for the same normalized input to be blocked after the current unavailable response, so that the client avoids redundant stub calls.
17. As a fan, I want the page to detect when my current form matches a saved itinerary, so that I can reuse existing persisted work instead of generating again.
18. As a fan, I want saved itineraries to load on the page, so that I can revisit plans that already exist.
19. As a fan, I want saved itineraries ordered according to the backend history contract, so that the newest plans appear first.
20. As a fan, I want saved itinerary cards to show title, city, date, party size, pace, item count, and update time, so that I can scan my plans quickly.
21. As a fan, I want to select a saved itinerary, so that I can inspect the full persisted aggregate.
22. As a fan, I want selected itinerary details to show ordered items, source type, area, start and end times, description, and route context, so that I can understand the plan without a separate endpoint.
23. As a fan, I want empty saved-history states to look intentional, so that a new account does not feel broken.
24. As a fan, I want history loading and error states with retry, so that temporary API failures are recoverable.
25. As a fan, I want the save action to avoid creating fake persisted plans while generation is unavailable, so that saved data remains canonical.
26. As a fan, I want already persisted itineraries to show as saved, so that the page does not imply extra action is required.
27. As a fan, I want a share button that copies a private app URL for the selected itinerary, so that I can return to or send the same app context without creating public sharing semantics.
28. As a fan, I want opening a URL with a selected itinerary identifier to focus that saved itinerary when it is in my history, so that copied private URLs are useful.
29. As a fan, I want invalid or unavailable selected itinerary identifiers to fall back to the normal saved-list state, so that stale links do not break the page.
30. As a fan, I want a map view placeholder that lists itinerary areas and route context, so that I can see where mapping will appear later.
31. As an operator, I want the map placeholder to make no paid routing or geospatial API calls, so that demos remain predictable and cost-free.
32. As an operator, I want no AI calls from the itinerary workspace in this phase, so that the system continues to minimize LLM dependence.
33. As a frontend developer, I want typed itinerary API client functions, so that components consume stable request and response contracts.
34. As a frontend developer, I want deterministic client-side input normalization for duplicate prevention, so that form matching is testable and independent of server implementation details.
35. As a frontend developer, I want duplicate prevention to complement, not replace, server-side input hash reuse, so that durable deduplication remains authoritative in the backend.
36. As a frontend developer, I want the itinerary workspace to follow existing React Query caching conventions, so that it does not poll or refetch aggressively.
37. As a frontend developer, I want the main app dashboard to expose the itinerary workspace, so that users can discover it alongside heatmap, city, and match intelligence.

## Implementation Decisions

- Build the itinerary workspace as a protected app route at `/app/itineraries`.
- Add a main protected app dashboard entry that links to the itinerary workspace.
- Use one primary itinerary page with a generation form, saved itinerary list, selected itinerary detail display, and map placeholder.
- Use the existing Phase 01 itinerary API contracts: `POST /itineraries/generate`, `GET /itineraries/me`, and the persisted itinerary DTOs.
- Treat `POST /itineraries/generate` as a real endpoint call that currently returns a structured `501 Not Implemented` response.
- Do not create fake generated itinerary content in the frontend while generation is unavailable.
- Do not expose a user-triggered save flow for generated results until a real generated draft exists. Existing persisted records render as saved.
- Load saved itineraries through the authenticated history endpoint with React Query.
- Use no polling and no automatic window-focus refetch for itinerary history or form-supporting API calls.
- The form uses host city reference data for city choices.
- The form may load matches for the selected city and keeps match selection optional.
- The form fields map directly to itinerary input: city, optional match, date, party size, interests, and pace.
- Interest options are fixed local values for this phase: food, fan zone, culture, family, nightlife, transit friendly, tourist spots, and venues.
- Pace is a fixed option set: relaxed, balanced, and packed.
- Client-side duplicate prevention uses a normalized input key composed from city, match, date, party size, sorted and trimmed interests, and pace.
- Client-side duplicate prevention blocks repeat generation for the same normalized input while a request is pending and after the current generation-unavailable response is received.
- Saved itinerary reuse detection compares normalized form input against normalized saved itinerary input rather than trying to reproduce the server's exact input hash.
- If a saved itinerary matches current form input, the UI highlights that saved itinerary and guides the user to inspect it.
- A selected saved itinerary is displayed inline rather than requiring a separate detail route in this phase.
- Share behavior is private app-link sharing only. The share button copies the itinerary workspace URL with a selected itinerary identifier in the query string.
- Opening the workspace with a selected itinerary query value should focus that itinerary when present in the authenticated user's loaded history.
- The map view is a placeholder panel that renders item locations, area labels, and approximate route context from the selected itinerary when available.
- No Mapbox, paid routing API, live places API, third-party geocoding, or AI endpoint is used in this phase.
- The route follows existing protected-app auth behavior: configured Supabase environments require a session, while local development without Supabase configuration remains viewable.
- The frontend should use typed itinerary API client functions and small helper modules for input normalization and share URL construction.
- The UI should match existing protected dashboard surfaces: restrained, operational, responsive, scan-friendly, and not a marketing page.

## Testing Decisions

- Test behavior through rendered UI and public API client/helper functions rather than private component internals.
- Add API client tests proving generation calls the expected endpoint, preserves the structured `501` error payload for UI handling, loads saved itinerary history, and throws predictably on non-OK history responses.
- Add input-normalization tests proving interest order, duplicate interests, and whitespace do not create different client duplicate keys.
- Add component tests proving the page does not call generation on load.
- Add component tests proving clicking Generate calls the generation endpoint with the form input.
- Add component tests proving duplicate Generate clicks for the same normalized input are blocked while pending.
- Add component tests proving repeat generation for the same normalized input is blocked after the generation-unavailable response.
- Add component tests proving saved itineraries load and render their scan-card data.
- Add component tests proving selecting a saved itinerary renders ordered item details and route context.
- Add component tests proving a matching saved itinerary is detected from current form input.
- Add component tests proving the share button copies a private app URL containing the selected itinerary identifier.
- Add component tests proving a query-selected itinerary is focused when present and handled gracefully when absent.
- Add component tests proving the map placeholder renders without calling external map or routing services.
- Reuse existing test patterns from match dashboard, city dashboard, and API client tests, including React Query test providers and mocked `fetch`.
- Run the frontend test suite, typecheck, and lint verification appropriate to the existing app scripts.

## Out of Scope

- Real itinerary generation.
- AI itinerary synthesis, AI summaries, RAG retrieval, or agent workflows.
- Client-side invented recommendation ranking or generated itinerary item creation.
- New backend endpoints or changes to the Phase 01 itinerary API contract.
- Database schema changes or Supabase migration changes.
- Public itinerary sharing between users.
- Collaborative itinerary editing.
- Deleting, renaming, or updating saved itineraries.
- Paid routing APIs, Mapbox routing, live places APIs, third-party geocoding, or live travel-time estimates.
- Persisting exact user coordinates, raw check-in data, private fan activity, or internal telemetry in itinerary UI payloads.
- A full interactive map implementation.
- Admin itinerary management UI.

## Further Notes

- The local checkout does not include the referenced `tickets/phase-05/05-03-itinerary-ui.md` file, so this PRD is based on the pasted ticket text, confirmed design decisions, the existing Phase 01 itinerary API contract, and current frontend patterns.
- The `/generate` endpoint returning `501` is expected behavior for this phase and should be represented as a staged integration state, not a generic failure.
- Server-side input hash reuse remains authoritative. Client duplicate prevention is a user-experience and cost-control layer only.
- The private share URL does not grant access to other users and should not imply public sharing semantics.
- Phase 06 can replace the generation-unavailable panel with a real generated draft flow while preserving the same form, duplicate-prevention, saved-history, selected-detail, and map-placeholder structure.
