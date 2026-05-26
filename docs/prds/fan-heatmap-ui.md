## Problem Statement

Fans and demo operators have no way to visualize where supporter activity is building across World Cup host cities. The backend fan intelligence slice already delivers a public `GET /cities/{city_id}/hotspots` API with scored, confidence-rated aggregate hotspot data seeded for every host city. Without a frontend surface, this data is invisible to users and unusable in demos.

The immediate need is a heatmap page that renders aggregate hotspots on a map, lets users filter by match, shows confidence and signal context per hotspot, and supports manual data refresh without continuous polling.

## Solution

Build a dedicated Fan Intelligence heatmap page at `/app/heatmap`. The page renders hotspot circles on an open-source interactive map (OpenStreetMap via react-leaflet). Hotspot circles are visually sized by supporter count and colored by score. Clicking a circle opens a popup with the area label, confidence badge, signal count, and evidence summary. A city dropdown lets the user switch between host cities, defaulting to their profile home city. A match filter dropdown narrows hotspots to a specific match in the selected city. A manual refresh button re-fetches hotspot data on demand and shows the last-updated timestamp. No polling occurs. No individual check-in pins are shown. The page is accessible from the main `/app` dashboard via a navigation link.

## User Stories

1. As an authenticated fan, I want to open the Fan Intelligence heatmap from the main app dashboard, so that I can discover where supporter activity is building in a host city.
2. As an authenticated fan, I want the heatmap to default to my home city when it loads, so that I see immediately relevant activity without selecting a city first.
3. As an authenticated fan, I want to switch between World Cup host cities using a dropdown, so that I can explore supporter activity in any city.
4. As an authenticated fan, I want to see hotspot circles on the map, so that I can understand at a glance where fans are gathering.
5. As an authenticated fan, I want larger circles to represent areas with more supporters, so that I can compare hotspot intensity visually.
6. As an authenticated fan, I want circle color to reflect the hotspot score, so that I can distinguish high-relevance hotspots from lower-relevance ones.
7. As an authenticated fan, I want to click a hotspot circle and see a popup with the area label, confidence badge, signal count, and evidence summary, so that I can understand the context behind each hotspot.
8. As an authenticated fan, I want confidence displayed as a labeled badge (High, Medium, or Low), so that I can immediately judge how reliable a hotspot's data is.
9. As an authenticated fan, I want the signal count to tell me how many supporters contributed to a hotspot, so that I understand the strength of the aggregate.
10. As an authenticated fan, I want the evidence summary to show me what factors drive a hotspot's score, so that I can understand why an area ranks highly.
11. As an authenticated fan, I want to filter hotspots by match using a dropdown populated from the selected city's match schedule, so that I can see activity related to a specific game.
12. As an authenticated fan, I want to clear the match filter and see all hotspots for the city, so that I can return to the full city view.
13. As an authenticated fan, I want a manual refresh button, so that I can fetch the latest hotspot data without the page polling continuously.
14. As an authenticated fan, I want to see a "Last updated" timestamp next to the refresh button, so that I know how fresh the current data is.
15. As an authenticated fan, I want the map viewport to center on the bounding box of the fetched hotspots when data loads, so that all hotspots are visible without manual pan or zoom.
16. As an authenticated fan, I want the map to fall back to a known center coordinate for the selected city when no hotspots are returned, so that the map always shows the correct geography.
17. As an authenticated fan, I want an empty state message when no hotspots exist for the selected city and match combination, so that I understand the absence of data rather than seeing a blank map.
18. As an authenticated fan, I want a loading indicator while hotspot data is fetching, so that I know the request is in progress.
19. As an authenticated fan, I want an error state with a retry option when the hotspot API fails, so that I can recover without reloading the full page.
20. As a demo operator, I want the heatmap to work correctly using seeded aggregate hotspot data, so that demos are compelling before organic check-in traffic exists.
21. As a privacy-conscious user, I want the heatmap to show only aggregate hotspot circles and never individual pins, so that no individual fan location is exposed.
22. As a user without a home city set in their profile, I want the city dropdown to start on a sensible default (first host city alphabetically), so that the heatmap is still usable during onboarding.

## Implementation Decisions

### New page and routing
- Add a new Next.js page at `app/app/heatmap/page.tsx` under the existing authenticated app layout.
- Add a navigation link or card on the main `/app` dashboard pointing to `/app/heatmap`.
- The page requires an authenticated session; redirect unauthenticated users to `/login` using the existing session pattern.

### Map rendering
- Use `react-leaflet` with OpenStreetMap tile layer (MIT licensed, zero cost, no API key required).
- Install `leaflet` and `react-leaflet` as frontend dependencies.
- Suppress Leaflet's default CSS import side-effect in the Next.js config or use a dynamic import with `ssr: false` to avoid hydration issues.
- Hotspot circles are rendered as `CircleMarker` components, not image markers.

### Hotspot visual encoding
- Circle radius is derived from `supporter_count` using square-root scaling with a defined minimum radius (so zero-supporter hotspots remain clickable).
- Circle fill color is interpolated along a fixed score gradient (e.g. light blue at score 0 → deep indigo at score 100) using inline style or a small lookup function.
- No third-party charting or visualization library is introduced.

### City selection
- The city dropdown is populated from the `hostCities` array already in `lib/reference-data.ts`.
- On page load, the selected city defaults to the user's `home_city_id` from their profile query. If `home_city_id` is absent or does not match a known host city, default to the first city in the `hostCities` array.
- Changing the city resets the match filter to "All matches" and re-fetches hotspots.

### Match filter
- On city selection, fetch the city's match schedule from `GET /matches?city_id={city_id}` using TanStack Query.
- Populate a "Filter by match" dropdown from the returned matches. Include an "All matches" option that omits the `match_id` query param.
- Selecting a match passes `match_id` to `GET /cities/{city_id}/hotspots?match_id={match_id}`.
- If the matches API is unavailable or returns zero matches, hide the match filter dropdown and show only hotspots without match filtering.

### Hotspot data fetching
- Fetch hotspots from `GET /cities/{city_id}/hotspots` using TanStack Query.
- Pass `match_id` when a match is selected; omit it for the "All matches" view.
- `staleTime` and `refetchInterval` are both disabled; the query only re-runs on explicit user action (city change, match change, or manual refresh button).
- The manual refresh button calls the query's `refetch()` method.
- Display the `updated_at` value from the most recently fetched hotspot as the "Last updated" timestamp. If no hotspots are present, show the fetch timestamp from the query metadata.

### Hotspot popup
- Clicking a `CircleMarker` opens a Leaflet `Popup` anchored to that circle.
- Popup content (rendered as a React component via `react-leaflet`):
  - **Area label**: `area_label` string.
  - **Confidence badge**: derived from the `confidence` float using thresholds: High (≥ 0.7), Medium (≥ 0.4), Low (< 0.4). Styled as a colored pill (green / amber / red).
  - **Signal count**: `supporter_count` displayed as "{n} signals".
  - **Evidence summary**: `ranking_factors` rendered as a readable key-value list. Unknown or empty `ranking_factors` shows "No additional evidence available."
  - **Last updated**: `updated_at` formatted as a relative time string.

### Map viewport
- After hotspots load, fit the map bounds to the bounding box of all returned hotspot centers using Leaflet's `fitBounds`.
- If no hotspots are returned, center the map on a hardcoded lat/lng lookup keyed by `city_id`. This lookup covers all 16 host cities and is co-located with the heatmap page or in a small utility module.
- Default zoom level for the empty/fallback state is 11.

### API client module
- Add a `lib/api/fan.ts` module following the pattern established by `lib/api/profile.ts`.
- Expose two functions: `fetchHotspots(cityId, matchId?, accessToken?)` and `fetchMatches(cityId)`.
- `fetchHotspots` targets `GET /cities/{city_id}/hotspots`. This endpoint is public; no access token is required.
- `fetchMatches` targets `GET /matches?city_id={city_id}`. This endpoint is also public.

### No polling constraint
- `refetchInterval`, `refetchIntervalInBackground`, and `refetchOnWindowFocus` are explicitly disabled on all heatmap queries.

### Privacy constraint
- Only aggregate hotspot data is fetched and rendered. The `fan_checkins` endpoint is never called from the heatmap page. No `user_id`, `checkin_id`, or raw coordinates appear in the UI.

## Testing Decisions

- Test the `lib/api/fan.ts` module by verifying that it constructs the correct URLs with and without `match_id`, and that it handles API error responses without throwing unhandled exceptions.
- Test the confidence badge utility by asserting the correct label and color class for boundary values (0.0, 0.39, 0.40, 0.69, 0.70, 1.0).
- Test the hotspot circle radius utility by asserting that `supporter_count = 0` yields the minimum radius and that higher counts yield proportionally larger radii.
- Test the city fallback center lookup by asserting that every `city_id` in `hostCities` resolves to a non-null lat/lng.
- Test the heatmap page component in isolation using mocked query responses: loading state, empty state, error state, and populated state with at least two hotspots.
- Test that the match filter dropdown is hidden when the matches query returns zero results.
- Test that selecting a match causes `fetchHotspots` to be called with the correct `match_id`.
- Test that the refresh button calls `refetch()` and updates the "Last updated" timestamp.
- Follow the existing React component testing patterns in the codebase. If no component tests exist yet, use React Testing Library with Jest or Vitest consistent with the project's test tooling.
- Do not test Leaflet rendering internals — only test the data flow and the React component surface.

## Out of Scope

- Fan check-in UI (creating or viewing personal check-ins).
- Venue discovery or paid map integrations (Mapbox, Google Maps).
- Realtime hotspot streaming or WebSocket updates.
- Automatic background polling or periodic refresh.
- Team-to-match-ID resolution (team picker is deferred until the matches API exposes team IDs per match).
- AI-generated evidence summaries or LLM-based hotspot explanations.
- Recommendation or itinerary flows driven by hotspot data.
- Push notifications when hotspots change.
- Administrative tools for managing or moderating hotspot data.
- Mobile-native or PWA-specific map interactions (pinch zoom, native gestures).
- Hotspot history or trend views.

## Further Notes

- The `GET /matches` API response schema was not fully verified at PRD time. Before implementing the match filter dropdown, confirm that the response includes a human-readable match label (e.g. team names or match title) and a `match_id` UUID. If only `match_id` is returned without a label, the dropdown will display raw IDs, which is acceptable for the initial slice.
- Leaflet requires a CSS import that can conflict with Next.js App Router SSR. Use `dynamic(() => import(...), { ssr: false })` for the map component to avoid hydration errors.
- The hardcoded city center lat/lng lookup is a one-time cost. If `hostCities` in `lib/reference-data.ts` is extended to include coordinates in a future migration, the fallback lookup can be removed.
- Seeded hotspot data in the database is the acceptance-criteria baseline. The UI must render correctly with that data and need not degrade gracefully for a completely empty database (that is an operational concern, not a UI concern).
- The `confidence` threshold boundaries (0.4, 0.7) are arbitrary defaults. They should be validated against actual seeded data values before shipping so that no single label category is empty in the demo.
