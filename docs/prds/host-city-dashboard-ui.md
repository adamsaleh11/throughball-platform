## Problem Statement

Throughball has source-backed host city, match, fan hotspot, venue, event, and tourist spot APIs, but users do not yet have a single polished city-level surface that turns those deterministic backend records into an operational host city dashboard. Today a fan can reach match intelligence and the fan heatmap separately, while the city guide backend data remains invisible in the product.

This matters now because the platform needs a low-cost, demo-ready city dashboard that proves the deterministic city guide architecture without introducing paid map embeds, large media assets, runtime third-party lookups, or automatic AI calls. Fans, demo operators, and interviewers should be able to choose a host city and immediately understand upcoming matches, aggregate fan activity, venues, events tonight, tourist spots, and where an AI concierge will eventually enter the workflow.

## Solution

Build a protected host city dashboard at a city-specific route. The dashboard loads city detail, upcoming matches, fan hotspots, venues, events, and tourist spots through existing public APIs and caches them with React Query. It presents a restrained operational dashboard with a city hero, section-level loading/error/empty states, and a city selector for moving between host cities.

The dashboard must not auto-call AI. The AI concierge is an entry point only: opening the page does not trigger any concierge network request, and clicking the entry only changes local UI state until a later AI integration ticket exists.

The page should work for all seeded host cities. If the URL contains a city ID that is not in the frontend host city catalog, the user sees a clear not-found state with links to valid cities. If the city is known locally but the backend cannot load its detail, the user sees a retryable fetch-failure state. Sparse category data is expected and should render honest empty states rather than fake records.

## User Stories

1. As an authenticated fan, I want to open a host city dashboard for a specific city, so that I can explore that city directly from a shareable URL.
2. As an authenticated fan, I want the app home to send me toward my preferred city when available, so that city discovery feels personal without new backend work.
3. As an authenticated fan without a saved preferred city, I want the dashboard entry to use my last selected city when available, so that returning to city discovery preserves my context.
4. As an authenticated fan without profile or browser city context, I want the dashboard entry to default to Toronto, so that the route always has a valid deterministic fallback.
5. As a local developer without Supabase frontend configuration, I want the city dashboard to remain viewable in local development, so that frontend work does not require hosted auth for every run.
6. As an unauthenticated visitor in a configured Supabase environment, I want protected app routes to redirect to login, so that private app surfaces stay consistent with the rest of the app.
7. As a fan, I want a city selector on the dashboard, so that I can switch between all supported host cities.
8. As a fan, I want changing the selected city to update the URL, so that the current dashboard can be bookmarked or shared.
9. As a fan, I want the selected city to be persisted in browser storage, so that the app can reopen the most recent city without a schema change.
10. As a fan, I want the hero to show city name, country, stadium, timezone, and useful counts from loaded data, so that I immediately understand the city context.
11. As a fan, I want the hero to use lightweight local styling rather than paid or heavy media, so that the dashboard opens quickly and costs nothing extra.
12. As a fan, I want upcoming matches for the selected city, so that I can see the football context driving city activity.
13. As a fan, I want upcoming matches ordered deterministically by kickoff time when available, so that the schedule is predictable.
14. As a fan, I want an empty match state when no matches are returned, so that sparse schedule data is not misrepresented.
15. As a fan, I want fan hotspots summarized in a ranked list, so that I can see where aggregate supporter activity is building without opening a map.
16. As a fan, I want a prominent link from hotspots to the full fan heatmap, so that I know where the map experience lives.
17. As a fan, I want hotspot cards to show area, score, confidence, supporter count, and updated time when available, so that the ranking is explainable from backend data.
18. As a fan, I want venues for the selected city, so that I can discover sourced places relevant to the city guide.
19. As a fan, I want the venues section to be named honestly, so that the UI does not imply recommendation scoring that the backend has not provided.
20. As a fan, I want venue cards to show type, area, amenities, tags, and source attribution when available, so that I can evaluate records without AI synthesis.
21. As a fan, I want events tonight for the selected city, so that I can see timely city activity near the match experience.
22. As a fan, I want “tonight” to be calculated using the selected city timezone, so that viewing another city does not silently use my browser timezone.
23. As a fan, I want an explicit timing-unavailable state if a selected city has no timezone, so that the app does not show wrong event windows.
24. As a fan, I want tourist spots for the selected city, so that I can find sourced public attractions near the World Cup experience.
25. As a fan, I want tourist spot cards to show type, area, tags, and source attribution when available, so that city exploration remains source-backed.
26. As a fan, I want each dashboard section to load independently, so that one failing category does not make the whole dashboard unusable.
27. As a fan, I want section-level retry actions on category fetch failures, so that I can recover without reloading the whole page.
28. As a fan, I want invalid city IDs to show “City not found” with valid city choices, so that broken links are understandable.
29. As a fan, I want known-city backend failures to show “Could not load city” with retry, so that temporary API issues are distinct from invalid routes.
30. As a demo operator, I want opening the dashboard to make no AI or paid third-party calls, so that demos are low-cost and predictable.
31. As a demo operator, I want API responses cached with React Query, so that repeated navigation does not hammer the backend.
32. As a demo operator, I want empty states to be polished, so that sparse seed data does not make the dashboard feel broken.
33. As a developer, I want city guide API fetchers typed in the frontend, so that UI components consume stable API contracts.
34. As a developer, I want the concierge entry behavior tested to ensure no fetch happens on click, so that later changes do not accidentally introduce AI cost.
35. As a developer, I want invalid city routing, empty sections, and city-timezone event filtering covered by tests, so that the highest-risk dashboard behaviors stay stable.

## Implementation Decisions

- Build the host city dashboard as a city-specific protected app route using the selected host city ID in the URL.
- Add an app-home dashboard entry that resolves the target city in this order: authenticated profile preference from the existing profile API, browser last-selected-city storage, then Toronto.
- Do not add profile schema or migration work for this ticket. Existing `user_preferences.home_city_id` may be read through the profile API when available.
- Persist manual city selection to browser storage using a dashboard-specific key. Browser storage is only a convenience fallback and must not be treated as authoritative backend preference data.
- Validate the route city ID against the frontend host city catalog before fetching city detail. Invalid local city IDs render a not-found state with available city choices.
- Fetch known city details from the city guide city detail API. Backend not-found or storage failures for known city IDs render a retryable city-load failure state.
- Load matches, hotspots, venues, events, and tourist spots using existing public APIs and React Query.
- Do not include transport hubs in the initial dashboard because the ticket acceptance criteria names city hero, upcoming matches, fan hotspots, venues, events tonight, tourist spots, and AI concierge entry.
- Cache dashboard API responses with React Query. Use no polling, no automatic window-focus refetching, and conservative stale times appropriate for static guide data.
- Keep category queries independent after city validation so each section can render loading, data, empty, or error states separately.
- Use a lightweight deterministic CSS city visual keyed from city identity. There are no existing local city image assets in the frontend checkout, and this ticket must not introduce large videos or paid map embeds.
- The hero must use only loaded city data and derived section counts. It must not invent editorial claims.
- Upcoming matches use the existing matches API filtered by city ID and are displayed in kickoff order when kickoff data is available.
- Fan hotspots are shown as a list summary on the dashboard, not an embedded map. A prominent link directs users to the full fan heatmap page.
- The hotspots section copy should explicitly indicate that the full map is available from the Fan Heatmap page.
- Rename the venue section to “Venues” rather than “Recommended venues” until a backend recommendation or scoring contract exists.
- Venue, event, and tourist spot cards expose source attribution when the API provides source name and URL.
- “Events tonight” must calculate the query window from the selected city timezone. If city timezone is missing, do not fall back to browser time; render an explicit timing-unavailable empty state.
- The city timezone implementation may use platform `Intl` APIs rather than adding a date library if that keeps the dependency surface smaller.
- The AI concierge entry is local UI only. Page load must not call AI, and clicking the entry must not call AI or any placeholder endpoint.
- The dashboard design should match the existing protected app and match dashboard style: restrained, operational, dense enough to scan, and responsive across mobile and desktop.
- Avoid nested cards, large decorative marketing heroes, paid map embeds, large media assets, and one-color decorative palettes.
- Frontend API clients should follow existing API module patterns and share common response metadata and pagination types where practical.
- The route should remain compatible with local-first development. If Supabase is not configured, local dev may render the dashboard without redirecting to login, matching the existing heatmap behavior.

## Testing Decisions

- Test behavior through rendered UI and public API client functions rather than private component internals.
- Add API client tests proving city guide fetchers call the expected city-scoped endpoints, include event date filters when provided, and throw on non-OK responses.
- Add component tests proving a valid city dashboard renders city context and API-backed sections.
- Add component tests proving category empty states render independently for matches, hotspots, venues, events, and tourist spots.
- Add component tests proving invalid route city IDs render a city-not-found state with available city options and do not call city detail APIs.
- Add component tests proving known-city detail failures render a retryable load-failure state, distinct from invalid route IDs.
- Add tests proving the concierge entry does not call `fetch` or any AI/network endpoint on page load or click.
- Add tests for the selected-city resolution order where practical: profile preference, browser last-selected-city, then Toronto.
- Add tests for event-window behavior: a city with timezone sends a city-local tonight window, while a missing timezone renders timing unavailable rather than querying with browser-local dates.
- Run the frontend test suite, typecheck, and lint/build verification appropriate to the existing app scripts.

## Out of Scope

- Backend schema changes.
- New profile preference fields or migrations.
- Backend venue recommendation scoring.
- Client-side invented venue scoring presented as authoritative recommendation logic.
- Transport hub UI.
- Mapbox, paid map embeds, or new paid geospatial services.
- Large videos or heavyweight city media assets.
- Runtime third-party city, event, venue, or tourism API calls.
- AI concierge implementation, AI chat, AI itinerary generation, RAG retrieval, or automatic AI synthesis.
- Admin curation UI.
- Real-time dashboard updates or polling.
- Writing profile preference changes back to Supabase when a user changes the city selector.

## Further Notes

- The prompt referenced `tickets/phase-05/05-02-city-dashboard-ui.md`, but that file is not present in the checkout. This PRD uses the provided ticket text, the Phase 01 host city backend PRD, and the current frontend/backend code as source context.
- Profile city personalization is available through the existing nested profile response, backed by `user_preferences.home_city_id`. The field is not on `profiles`.
- The frontend checkout has no `public` asset directory and no local city image assets. The implementation should therefore use deterministic CSS visuals unless a separate asset ticket adds optimized local images.
- City timezone correctness is a product requirement. Browser-local time must not be used as a fallback for city-scoped event filtering.
- Sparse data is acceptable. Empty lists from the backend should be treated as truthful city guide coverage, not as an error.
- Future backend work can introduce deterministic venue recommendation scoring and transport hub dashboard modules without changing the route shape.
