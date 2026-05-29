## Problem Statement

Throughball has host city, match, and aggregate fan hotspot foundations, but it does not yet have a complete host city intelligence backend. Fans, demo operators, and future MCP tools need reliable city-level context around venues, events, tourist spots, and transport hubs across every World Cup host city. Today that information is not normalized into the platform, which means city guide, venue discovery, hotspot explanation, and itinerary flows would either depend on ad hoc external lookups or incomplete hardcoded data.

This matters now because the platform's strongest technical thesis is deterministic, privacy-preserving fan and city operations intelligence. The backend should own structured facts, filtering, attribution, and scoring inputs before any AI layer explains results. The city guide backend must therefore provide real sourced data for all existing host cities, run without live third-party APIs during demos, and avoid dummy or invented records.

## Solution

Build a source-backed host city intelligence backend that uses the existing host city catalog as the canonical city identity layer and adds city-scoped guide data for venues, city events, tourist spots, and transport hubs. Public APIs expose deterministic, paginated, filterable records for every existing host city. Records must include source attribution so operators and AI layers can trace where claims came from.

The backend will persist curated seed data in Supabase and read from Supabase at runtime. Free public APIs and open data sources may be used during offline import or seed generation, but API requests must not call Google Places, paid map APIs, scraped live event sites, or any live third-party data dependency. If reliable sourced data is unavailable for a city/category, the API should return an empty list rather than fake completeness.

The feature should support all World Cup host cities already present in the platform: Toronto, Vancouver, Guadalajara, Mexico City, Monterrey, Atlanta, Boston, Dallas, Houston, Kansas City, Los Angeles, Miami, New York/New Jersey, Philadelphia, San Francisco Bay Area, and Seattle. Toronto and Vancouver may have denser initial coverage where official open data is strong, but every city must have working routes, city detail, and valid category responses.

## User Stories

1. As a public user, I want to list all supported host cities, so that I can choose a city to explore.
2. As a public user, I want to fetch details for one host city, so that I can understand its basic World Cup city context.
3. As a public user, I want every host city route to work for all 16 host cities, so that the product does not feel limited to Toronto and Vancouver.
4. As a public user, I want to fetch venues for a city, so that I can find sourced places relevant to match-day fan activity.
5. As a public user, I want to filter venues by type, area, amenities, and tags, so that I can narrow results without AI guessing.
6. As a public user, I want venue responses to include source attribution, so that I can trust where the venue data came from.
7. As a public user, I want venue responses to include public location context, so that maps and recommendations can place the venue geographically.
8. As a public user, I want venue responses to avoid user check-in or private telemetry fields, so that public city guide data remains separate from private fan activity.
9. As a public user, I want to fetch city events for a host city, so that I can see relevant sourced events around the city guide experience.
10. As a public user, I want to filter city events by type, date range, and tags, so that I can find relevant events deterministically.
11. As a public user, I want stale or uncertain event data excluded rather than invented, so that event results remain credible.
12. As a public user, I want to fetch tourist spots for a city, so that I can discover sourced public attractions near the World Cup experience.
13. As a public user, I want to filter tourist spots by type, area, and tags, so that guide tools can produce focused results.
14. As a public user, I want to fetch transport hubs for a city, so that I can understand airport, rail, transit, and stadium-access context.
15. As a public user, I want to filter transport hubs by type, so that clients can distinguish airports, stations, transit hubs, and stadium-adjacent access points.
16. As a fan using a future recommendation flow, I want city guide records to connect cleanly to hotspots and matches through city IDs, so that recommendations can combine city context with fan intelligence.
17. As a demo operator, I want the demo to run without live third-party APIs, so that network outages, API keys, quotas, or paid providers cannot break the demo.
18. As a demo operator, I want real sourced seed data rather than dummy data, so that the project reads as credible host city intelligence.
19. As a backend developer, I want all city guide tables to reference the canonical host city table, so that city IDs stay consistent across profiles, matches, hotspots, and guide data.
20. As a backend developer, I want guide APIs to use the same response envelope and observability metadata as existing APIs, so that clients receive consistent contracts.
21. As a backend developer, I want city guide filtering to happen in backend/store queries, so that LLMs are not used for sorting or filtering.
22. As a backend developer, I want guide records to include stable IDs, tags, and source fields, so that later MCP tools and recommendation systems can compose them safely.
23. As a backend developer, I want seed imports to preserve source name, source URL, data origin, and verification date, so that records can be audited and refreshed later.
24. As an operator, I want city guide tables protected by public-read RLS policies only, so that clients cannot mutate curated data.
25. As an operator, I want unknown city IDs to return structured not-found errors, so that bad clients and broken MCP calls are obvious.
26. As an operator, I want storage failures to return structured unavailable errors with request metadata, so that clients can recover predictably.
27. As a data curator, I want the system to accept sparse category coverage, so that we can ship truthful data without fabricating records.
28. As a data curator, I want official municipal, tourism, open data, Wikidata, or OpenStreetMap-derived sources tracked per record, so that source quality is visible.
29. As an AI integration developer, I want RAG to be optional explanatory context only, so that structured Supabase records remain the source of truth.
30. As an AI integration developer, I want AI synthesis to explain selected records rather than decide which records exist, so that the platform stays deterministic-first.
31. As a tester, I want migration and API tests to prove all required tables, RLS policies, filters, and source fields exist, so that regressions are caught before demo use.
32. As a tester, I want seeded data checks for all host cities, so that the implementation does not accidentally support only Toronto and Vancouver.

## Implementation Decisions

- Use the existing host city table as the canonical city identity model. Do not create a separate city identity table.
- Add city guide persistence using the new tables `venues`, `city_events`, `tourist_spots`, and `transport_hubs`.
- Each city guide table references the canonical host city ID.
- All guide records include stable IDs, city ID, name/title, type/category, area label where available, tags, public location fields where available, source name, source URL, data origin, and last verified timestamp.
- Public place coordinates are allowed for venues, tourist spots, and transport hubs because they describe public places, not user locations. User check-in coordinates remain private and must not appear in guide APIs.
- Use structured source fields rather than burying attribution in free-form descriptions.
- Runtime API requests read only from Supabase. Free public APIs and open datasets may be used only for offline import, curation, or seed generation.
- Do not use Google Places API, paid map APIs, scraped live event sites, or runtime calls to third-party APIs for this feature.
- Use official city, municipal open data, official tourism, official venue, Wikidata, or OpenStreetMap-derived sources when license and attribution requirements are acceptable.
- Prefer official city or tourism data over generic community datasets when both are available.
- Do not create dummy records. If a category lacks reliable sourced data for a host city, return an empty paginated list for that category.
- Support all existing World Cup host cities in the platform, not only Toronto and Vancouver.
- Toronto and Vancouver may have richer initial records where official open data is easier to consume, but API behavior must be consistent for every host city.
- Add `GET /cities/{city_id}` for city detail.
- Add `GET /cities/{city_id}/venues` for city-scoped venues.
- Add `GET /cities/{city_id}/events` for city-scoped events.
- Add `GET /cities/{city_id}/tourist-spots` for city-scoped tourist spots.
- Add `GET /cities/{city_id}/transport-hubs` so the transport hub table is reachable by clients and MCP tools.
- Preserve backward-compatible behavior for existing `GET /cities` clients.
- List endpoints use standard pagination with default page 1, default page size 20, and maximum page size 100.
- Venue filtering supports venue type, area label, amenity, tags, page, and page size.
- Event filtering supports event type, start date lower bound, start date upper bound, tags, page, and page size.
- Tourist spot filtering supports spot type, area label, tags, page, and page size.
- Transport hub filtering supports hub type, area label, tags, page, and page size.
- Unknown city IDs return structured not-found errors rather than empty category lists.
- Storage failures return structured storage-unavailable errors.
- All successful and error responses include observability metadata with request ID, trace ID, latency, retries, and degraded execution.
- Enable RLS for all new guide tables.
- Add public read policies for guide tables and do not add public insert, update, or delete policies.
- Build the backend using the existing route, model, core service, store, and dependency override patterns already used by the FastAPI app.
- Keep RAG out of the authoritative API path. RAG may later retrieve source documents for explanation, but it must not decide available records, filters, rankings, or API output.
- Update the API contract documentation so city guide DTOs and route paths match the new city-scoped APIs.

## Testing Decisions

- Test API behavior at route and service-contract boundaries rather than testing private implementation details.
- Add migration-contract coverage proving the four new tables exist.
- Add migration-contract coverage proving the guide tables reference the canonical host city IDs.
- Add migration-contract coverage proving required source attribution fields exist.
- Add migration-contract coverage proving RLS is enabled and public read policies exist without public write policies.
- Add seed-data coverage proving all existing host cities are represented by the city guide migration or explicitly supported by empty category responses.
- Add route tests for `GET /cities/{city_id}` success and unknown-city not found behavior.
- Add route tests for each city-scoped list endpoint returning the expected envelope, pagination, and observability metadata.
- Add route tests for venue filters including type and amenity.
- Add route tests for event filters including date range and event type.
- Add route tests for tourist spot and transport hub filters.
- Add service/store tests proving filters are passed into deterministic Supabase queries.
- Add tests proving source fields are returned in public guide payloads.
- Add tests proving guide payloads do not include private fan fields such as user IDs, check-in IDs, raw check-in timestamps, or user telemetry.
- Follow the existing FastAPI dependency override pattern for route tests.
- Keep Supabase integration tests optional unless real local/test Supabase environment variables are present.
- Run the existing API test suite to ensure `GET /cities`, match APIs, fan hotspot APIs, and profile flows remain compatible.

## Out of Scope

- Runtime Google Places, paid map, paid event, or paid tourism APIs.
- Scraping live event sites.
- Fake, dummy, or invented city guide records.
- Frontend city guide UI.
- Admin curation UI.
- Automated scheduled refresh jobs.
- Live event freshness guarantees.
- Venue recommendation scoring beyond basic deterministic filters.
- Itinerary generation.
- AI-generated ranking, AI filtering, or LLM-based source selection.
- RAG ingestion pipeline implementation.
- Real-time fan operations dashboards.
- User check-in changes beyond preserving privacy boundaries with guide data.
- Full data licensing/legal review beyond storing clear source attribution fields for each record.

## Further Notes

- The source ticket path was not present in the checkout, so the provided ticket text and follow-up decisions are the source of truth.
- This PRD intentionally upgrades the original "Toronto and Vancouver first" line: the implementation must work for all existing host cities. Toronto and Vancouver may receive more complete initial records, but the system cannot be architected as a two-city feature.
- Public source discovery performed during planning confirmed that official FIFA host city material, municipal open data portals, Wikidata Query Service, and OpenStreetMap/Overpass-style data are plausible source classes. The implementation still needs per-record source validation and attribution before seeding.
- RAG and the separate AI knowledge base should be treated as explanatory support, not the product database. Supabase remains the source of truth for API and MCP behavior.
- The most important quality bar is credibility: sparse real data is acceptable; broad fake data is not.
- Future work can add curation tooling, refresh scripts, confidence scoring for source quality, proximity scoring, venue-to-hotspot joins, itinerary APIs, and operator dashboards.
