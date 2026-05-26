# Plan: Fan Heatmap UI

> Source PRD: docs/prds/fan-heatmap-ui.md

## Architectural decisions

- **Routes**: New page at `/app/heatmap`; navigation link added to `/app` dashboard
- **Map library**: `react-leaflet` + OpenStreetMap tiles (MIT, zero cost); map component loaded with `dynamic(..., { ssr: false })` to avoid Next.js hydration issues
- **API client**: `lib/api/fan.ts` following the `lib/api/profile.ts` pattern; exposes `fetchHotspots(cityId, matchId?)` and `fetchMatches(cityId)`
- **Data fetching**: TanStack Query; `refetchInterval`, `refetchIntervalInBackground`, and `refetchOnWindowFocus` all disabled; refresh is manual only
- **Key models**: `Hotspot` (hotspot_id, city_id, match_id, area_label, center{lat,lng,precision}, score, confidence, supporter_count, ranking_factors, updated_at); `Match` (id, label/title, city_id)
- **Auth**: Page requires authenticated Supabase session; hotspot and match API calls are public (no token required)
- **City reference data**: `hostCities` from `lib/reference-data.ts` is the source of truth for city IDs and names
- **Visual encoding**: Circle radius = `Math.sqrt(supporter_count) * scaleFactor` with a defined minimum; fill color interpolated from score (0–100) along a fixed gradient
- **Confidence thresholds**: High ≥ 0.7 (green), Medium ≥ 0.4 (amber), Low < 0.4 (red)
- **Signal count**: maps to `supporter_count`
- **Evidence summary**: maps to `ranking_factors` rendered as key-value list
- **City fallback centers**: hardcoded lat/lng lookup keyed by city ID, covering all 16 host cities

---

## Phase 1: Scaffold + static hotspot map

**User stories**: 1, 5, 6, 18, 19, 20, 21

### What to build

Install `react-leaflet` and `leaflet`. Create `/app/heatmap` as a new authenticated page. Add `lib/api/fan.ts` with `fetchHotspots`. Fetch hotspots for a hardcoded default city on load. Render hotspot circles on an OpenStreetMap tile layer: radius derived from `supporter_count`, fill color derived from `score`. Show a loading spinner while fetching, an error state with retry, and an empty-state message when no hotspots are returned. Add a navigation link or card on the `/app` dashboard pointing to `/app/heatmap`. No individual pins are rendered — only aggregate circles.

### Acceptance criteria

- [ ] Navigating to `/app/heatmap` shows an interactive OpenStreetMap
- [ ] Hotspot circles appear on the map for the default city
- [ ] Circle size is visually proportional to `supporter_count`; circles with zero supporters have a minimum visible radius
- [ ] Circle fill color varies with `score`; high-score circles are visually distinct from low-score ones
- [ ] A loading indicator is shown while the hotspot request is in flight
- [ ] An error message and retry option appear when the API returns an error
- [ ] An empty-state message appears when the API returns zero hotspots
- [ ] No individual user pins are rendered
- [ ] A link or card on `/app` navigates the user to `/app/heatmap`
- [ ] `fetchHotspots` constructs the correct URL with and without `match_id`
- [ ] Radius utility returns the minimum radius for `supporter_count = 0` and a larger value for positive counts
- [ ] Score-color utility returns distinct color values at score 0, 50, and 100

---

## Phase 2: City selection + viewport fitting

**User stories**: 2, 3, 15, 16, 17, 22

### What to build

Add a city dropdown to the heatmap page header, populated from `hostCities`. On page load, resolve the user's `home_city_id` from the cached profile query and pre-select that city; fall back to the first city alphabetically if `home_city_id` is absent or unrecognised. Changing the city re-fetches hotspots for the new city and resets the match filter. After hotspots load, fit the map viewport to the bounding box of all returned hotspot centers. When no hotspots are returned, center the map using a hardcoded lat/lng lookup for the selected city at a default zoom level. Show a contextual empty-state message when the city+filter combination yields no hotspots.

### Acceptance criteria

- [ ] City dropdown lists all 16 host cities by name
- [ ] On load, the city matching `home_city_id` is pre-selected
- [ ] When `home_city_id` is absent, the first city alphabetically is selected
- [ ] Selecting a different city triggers a new hotspot fetch and updates the map
- [ ] After hotspots load, the map fits its viewport to include all hotspot circles
- [ ] When no hotspots exist, the map centers on the city's fallback lat/lng at zoom 11
- [ ] All 16 city IDs in `hostCities` resolve to a non-null fallback lat/lng
- [ ] An empty-state message is shown when the selected city has no hotspots

---

## Phase 3: Hotspot popup — confidence, signal count, evidence summary

**User stories**: 7, 8, 9, 10

### What to build

Clicking a hotspot circle opens a Leaflet popup anchored to that circle. The popup renders: the `area_label`, a confidence badge, signal count, evidence summary, and a last-updated timestamp. The confidence badge maps the `confidence` float to a labeled pill: High (≥ 0.7, green), Medium (≥ 0.4, amber), Low (< 0.4, red). Signal count displays as "{n} signals". Evidence summary renders `ranking_factors` as a readable key-value list; if `ranking_factors` is empty or absent, show "No additional evidence available."

### Acceptance criteria

- [ ] Clicking a hotspot circle opens a popup for that hotspot
- [ ] Popup shows the `area_label`
- [ ] Confidence badge shows "High" with green styling for confidence ≥ 0.7
- [ ] Confidence badge shows "Medium" with amber styling for 0.4 ≤ confidence < 0.7
- [ ] Confidence badge shows "Low" with red styling for confidence < 0.4
- [ ] Boundary values (0.0, 0.39, 0.40, 0.69, 0.70, 1.0) each map to the correct badge label
- [ ] Signal count displays as "{supporter_count} signals"
- [ ] Evidence summary renders each `ranking_factors` key-value pair as a readable line
- [ ] When `ranking_factors` is empty or absent, the popup shows "No additional evidence available"
- [ ] Popup shows the `updated_at` value as a timestamp

---

## Phase 4: Match filter + manual refresh

**User stories**: 11, 12, 13, 14

### What to build

Add `fetchMatches(cityId)` to `lib/api/fan.ts`. On city selection, fetch matches for that city and populate a "Filter by match" dropdown. Include an "All matches" option that omits `match_id` from the hotspot query. Selecting a match passes its `match_id` to `fetchHotspots` and re-fetches. Hide the dropdown entirely when the city has no matches. Add a manual refresh button that calls the hotspot query's `refetch()` method. Display a "Last updated" timestamp derived from `updated_at` on the most recent hotspot; update it after each refresh. Confirm that `refetchInterval` and `refetchOnWindowFocus` are both disabled.

### Acceptance criteria

- [ ] "Filter by match" dropdown is populated with the city's matches
- [ ] An "All matches" option is always the first item and omits `match_id` from the query
- [ ] Selecting a match re-fetches hotspots with the correct `match_id`
- [ ] Clearing the filter (selecting "All matches") re-fetches without `match_id`
- [ ] The match dropdown is hidden when the city's match list is empty
- [ ] The match filter resets to "All matches" when the city changes
- [ ] A "Refresh" button is visible on the heatmap page
- [ ] Clicking "Refresh" triggers a hotspot re-fetch
- [ ] A "Last updated" timestamp appears and updates after each refresh
- [ ] `refetchInterval` and `refetchOnWindowFocus` are confirmed disabled (no background polling occurs)
- [ ] `fetchMatches` constructs the correct URL with `city_id` as a query parameter
