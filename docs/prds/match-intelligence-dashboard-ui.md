# Match Intelligence Dashboard UI PRD

## Problem Statement

Throughball has deterministic World Cup match APIs for match detail, team stats, event timelines, and tactical momentum, but the web app does not yet expose a focused match intelligence view. Users can see fan hotspot intelligence, but they cannot open a match and inspect seeded match context, score, statistical comparison, timeline events, or tactical snapshots in one operational dashboard.

This matters now because later AI analyst work depends on a stable match page entry point. The product needs a frontend surface that proves the Phase 01 match APIs can power match intelligence without live sports providers, continuous polling, or AI-generated match facts.

## Solution

Build an authenticated match intelligence detail page in the Throughball app. The page will load one match from the URL, render deterministic seeded data from the existing match APIs, and give users a manual refresh control. It will display a compact match header, a score derived from match stats, team comparison stats, a tactical momentum chart, an event timeline, and an inert AI analyst panel that clearly indicates Phase 06 integration is not available yet.

The page will not include in-page match switching, live data feeds, polling, AI synthesis, or a new backend aggregation endpoint. Match selection remains outside this ticket, with the app landing page linking users into a seeded match detail route.

## User Stories

1. As an authenticated Throughball user, I want to open a match intelligence page from the app workspace, so that I can inspect match data in context.
2. As an authenticated Throughball user, I want the match ID to come from the URL, so that each match detail page is shareable within the app route structure.
3. As an authenticated Throughball user, I want the app landing page to expose a Match Intelligence entry point, so that I can discover the new dashboard.
4. As an authenticated Throughball user, I want the page to render the match teams, competition, stage, city, kickoff time, status, and tags, so that I understand the match context quickly.
5. As an authenticated Throughball user, I want to see the displayed score, so that I can understand the seeded match state at a glance.
6. As an authenticated Throughball user, I want the displayed score to come from match stats, so that score display follows the authoritative deterministic stat source.
7. As an authenticated Throughball user, I want timeline events to remain independent from the displayed score, so that seeded event gaps do not create confusing frontend behavior.
8. As an authenticated Throughball user, I want a team-by-team stats comparison, so that I can compare goals, possession, shots, shots on target, passes, corners, and fouls.
9. As an authenticated Throughball user, I want a momentum visualization from tactical snapshots, so that I can inspect deterministic tactical state without invented analysis.
10. As an authenticated Throughball user, I want an empty momentum state when snapshots are unavailable, so that absence of seeded data is handled honestly.
11. As an authenticated Throughball user, I want an event timeline ordered by match clock, so that key match events are easy to scan.
12. As an authenticated Throughball user, I want each event to show minute, stoppage minute when present, event type, team, player when available, and description when available, so that timeline rows are readable without raw IDs.
13. As an authenticated Throughball user, I want a manual refresh button, so that I can reload seeded match data on demand.
14. As an authenticated Throughball user, I do not want the page to poll continuously, so that the app respects low-cost runtime rules.
15. As an authenticated Throughball user, I want loading states that preserve the dashboard layout, so that the page does not feel unstable while data loads.
16. As an authenticated Throughball user, I want a clear page-level error when the match does not exist, so that broken or stale match links are understandable.
17. As an authenticated Throughball user, I want section-level errors for stats, events, or momentum failures, so that partial data issues do not hide the entire match detail when the match itself loads.
18. As an authenticated Throughball user, I want the AI analyst panel to be visible but unavailable, so that I can see where Phase 06 functionality will enter later.
19. As an authenticated Throughball user, I want the AI analyst ask button to be disabled with a tooltip explaining Phase 06 availability, so that the panel appears intentional rather than broken.
20. As a frontend developer, I want a dedicated match API client module, so that match dashboard data access does not expand the fan hotspot API client.
21. As a frontend developer, I want stable TypeScript contracts for match detail, stats, events, and momentum responses, so that dashboard components depend on explicit API shapes.
22. As a frontend developer, I want React Query configured without window-focus refetching or intervals for this page, so that data loading behavior enforces the cost rule.
23. As a frontend developer, I want one refresh action to refetch match detail, stats, events, and momentum, so that the user has a simple and predictable reload workflow.
24. As a frontend developer, I want the momentum chart implemented without a new charting dependency, so that the ticket stays small and aligned with the current dependency set.
25. As a tester, I want API-client tests for match endpoints, so that URL construction and error behavior are covered.
26. As a tester, I want component tests for score derivation, empty momentum, inert AI panel, and refresh behavior, so that the important acceptance criteria are proven through user-visible behavior.

## Implementation Decisions

- Add an authenticated match detail route under the existing app workspace using a URL-provided match ID.
- Do not add an in-page match selector for this ticket.
- Add a Match Intelligence entry point from the app landing page. It may link to a known seeded match route or use the first seeded match loaded from the existing match list API, but the detail page itself does not own match selection.
- Use the existing match API surface: match detail, match stats, match events, and match momentum.
- Do not add a dashboard aggregation endpoint. The frontend composes the existing small endpoints.
- Add a dedicated match API client module with typed response contracts for detail, stats, events, and momentum.
- Use React Query for data loading with window-focus refetching disabled, refetch intervals disabled, and no continuous polling.
- Provide one manual refresh action that refetches all dashboard queries.
- Treat match stats as authoritative for displayed score.
- Treat match events as authoritative only for the timeline; event rows do not reconcile or override the displayed score.
- Render the momentum chart using local SVG or HTML primitives. No charting library is currently installed in the web app, and this ticket should not introduce one.
- Render empty states for missing stats, missing events, and missing momentum without synthesizing data.
- Render a page-level not-found or unavailable state when match detail cannot be loaded.
- Render section-level error states when stats, events, or momentum fail independently after match detail loads.
- Render an AI analyst entry panel with an input affordance and a disabled ask button.
- The disabled AI ask button uses a tooltip with the message: "Available after Phase 06 integration."
- The AI analyst panel must not call the AI runtime, generate mock responses, or invoke any backend endpoint.
- Keep the visual style consistent with the existing authenticated app: compact headers, bordered operational panels, muted metadata, lucide icons, and no marketing-style hero.
- No schema changes are required.
- No backend API changes are required unless implementation discovers a contract mismatch in the existing Phase 01 endpoints.
- No live sports provider, websocket, background sync, or continuous refresh behavior is introduced.

## Testing Decisions

- Tests should verify external behavior and user-visible contracts rather than implementation internals.
- API-client tests should cover match detail, stats, events, and momentum URL construction.
- API-client tests should cover non-OK responses throwing clear errors.
- Component tests should cover score derivation from stats and should document that stats win over event-derived assumptions.
- Component tests should cover the empty momentum state.
- Component tests should cover the inert AI analyst panel, including the disabled ask button and Phase 06 tooltip text.
- Component or page tests should cover manual refresh triggering all dashboard data reloads without relying on polling.
- Component tests are supported by the current web test setup: Vitest uses jsdom and Testing Library is already used for React component tests.
- Existing fan API and confidence badge tests provide local precedent for API-client and component-level coverage.

## Out of Scope

- Public match dashboard routes outside the authenticated app workspace.
- In-page match switching or a full match-list page.
- Phase 06 AI analyst runtime wiring.
- AI-generated tactical summaries, score explanations, or event analysis.
- Backend aggregation endpoints for the dashboard.
- New database schema, migrations, or seed-data changes.
- Live sports APIs, provider SDKs, polling, streaming, cron jobs, or background refresh.
- Adding a charting dependency.
- Reconciling mismatches between seeded stats and seeded events beyond documenting source authority in the UI behavior and tests.

## Further Notes

- The source ticket file was not present in the checkout; the pasted ticket content is the source of truth.
- The exact ticket referenced "Doc 1 ticket 07-01," but the existing backend match API PRD and plan are named around World Cup match APIs and importer.
- The current web app has no charting dependency matching Recharts, Chart.js, D3, Visx, or Nivo, so the momentum chart should be hand-rolled.
- The current web app already supports React component tests through Vitest, jsdom, and Testing Library.
- Follow-up work should add a real match-list or match-selection experience if product needs users to browse across matches.
- Phase 06 should replace the inert analyst panel with a runtime-backed question flow while preserving the deterministic match dashboard as context.
