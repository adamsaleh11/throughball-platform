## Problem Statement

Throughball needs a low-cost authentication and user profile foundation before user-specific recommendations, check-ins, onboarding, and protected app surfaces can work. The current repo has a Next.js frontend and FastAPI backend scaffold, but no auth provider, profile persistence, protected routes, or row-level data isolation. This blocks any feature that depends on knowing the current user while preserving privacy.

This matters now because future platform systems need deterministic, user-scoped preferences without adding paid auth services or storing unnecessary personal data.

## Solution

Implement Supabase Auth directly in the Next.js frontend for signup, login, logout, session refresh, and route protection. Supabase Auth owns credentials and email identity. FastAPI remains stateless and validates Supabase bearer tokens before serving protected profile APIs.

Create Supabase database schema for private user profile data, preferences, and favorite team relationships. A single database trigger provisions the minimal profile and preferences rows when a Supabase auth user is created. Row Level Security ensures users can only access their own private profile, preferences, and favorite team rows. Public reference data such as host cities and teams can be read for onboarding.

The frontend will expose signup, login, logout, onboarding, and a protected app surface. Onboarding updates the profile aggregate through FastAPI and uses `profile_completed` to decide whether an authenticated user should continue onboarding or enter the app.

## User Stories

1. As a new visitor, I want to sign up with email and password, so that I can create a Throughball account without a paid third-party auth provider.
2. As a new user, I want my profile row to be created automatically during signup, so that the app has a consistent account record even if the browser flow is interrupted.
3. As a returning user, I want to log in with email and password, so that I can access protected app features.
4. As an authenticated user, I want to log out, so that my session is cleared from the browser.
5. As an unauthenticated visitor, I want protected routes to redirect me to login, so that private app surfaces are not visible without a session.
6. As an authenticated user with incomplete onboarding, I want to be directed to onboarding, so that I can finish basic setup before using personalized features.
7. As an authenticated user, I want onboarding to be skippable or partial, so that missing optional preferences do not block me from using the app.
8. As an authenticated user, I want to set a display name and optional avatar URL, so that future social and fan features can show a lightweight identity.
9. As an authenticated user, I want to choose a home city, so that the app can personalize match and venue discovery.
10. As an authenticated user, I want to choose favorite teams, so that recommendations and future fan features can use real relational team affinity.
11. As an authenticated user, I want to choose preferred match tags from a controlled list, so that recommendations can use clean deterministic signals.
12. As an authenticated user, I want profile data returned in a nested shape, so that profile identity and preferences can evolve independently.
13. As a user, I do not want my private profile data readable by other users, so that my preferences remain isolated.
14. As a developer, I want RLS policies to enforce tenant isolation, so that database access is safe even if application code has a bug.
15. As a developer, I want one real RLS integration test with two users, so that tenant isolation is proven through Supabase-backed behavior.
16. As a developer, I want FastAPI profile APIs to include request metadata, so that protected requests are traceable without adding hosted observability.
17. As a developer, I want missing Supabase env vars not to break local health checks or frontend builds, so that local-first development remains easy.
18. As an operator, I want production email confirmation documented separately from dev settings, so that local testing stays fast while production can be hardened.

## Implementation Decisions

- Supabase Auth is used directly from the Next.js frontend. FastAPI does not proxy signup, login, logout, or refresh.
- FastAPI protects profile APIs with `Authorization: Bearer <Supabase access token>`.
- JWT validation prefers Supabase JWKS via `SUPABASE_JWKS_URL`; local/dev fallback can be documented if required.
- FastAPI profile APIs use the caller's user token when querying Supabase so RLS is exercised.
- Profile API responses use nested shape: `profile`, `preferences`, and `meta`.
- Minimal response metadata for this ticket is `request_id`, `trace_id`, and `degraded`.
- `profiles` stores `id`, `display_name`, `avatar_url`, `profile_completed`, `created_at`, and `updated_at`.
- `user_preferences` stores `user_id`, `home_city_id`, `preferred_match_tags`, `created_at`, and `updated_at`.
- `user_favorite_teams` stores `user_id`, `team_id`, and `created_at` with a composite primary key.
- `favorite_team_ids` are not stored as arrays. Team affinity is modeled as a normalized many-to-many relationship.
- `preferred_match_tags` are stored as a text array constrained to an allowed controlled vocabulary.
- The initial allowed match tags are `rivalry`, `high_press`, `underdog`, `knockout`, and `fan_festival`.
- A single trigger on `auth.users` creates both `profiles` and `user_preferences`.
- `profile_completed` is explicit and computed by backend profile/onboarding writes, not manually controlled by users.
- A profile is considered complete when it has a display name plus either a home city or at least one favorite team.
- `avatar_url` is nullable text with a length constraint. Avatar upload/storage is out of scope.
- `host_cities` and `teams` are referenced as early domain tables. If absent, this ticket may create minimal FK target tables and seed enough rows to test onboarding.
- Public reference tables can be readable by anonymous and authenticated users.
- Private tables use RLS with `using` and `with check` policies so users can only access their own rows.
- `profiles` normal user insert is not allowed; the trigger owns creation.
- `user_preferences` insert is allowed for the authenticated owner to recover from failed provisioning.
- `user_favorite_teams` select, insert, and delete are allowed only for the authenticated owner.
- Frontend protected routing covers `/app/*`. `/onboarding` is soft-protected and can recover auth state before redirecting.
- Zustand remains installed but is not used for auth/session lifecycle.
- Supabase hosted free tier is acceptable. Dockerized local Supabase is out of scope.

## Testing Decisions

- Use behavior-level tests through public interfaces rather than implementation details.
- Add backend tests for missing/invalid auth returning `401`, profile response shape, profile update validation, and minimal response metadata.
- Add one opt-in RLS integration test using two real Supabase users/JWTs when Supabase test env vars are present. The test must prove user A cannot read or mutate user B's profile, preferences, or favorite team rows.
- Mock Supabase calls in regular backend tests so the normal suite does not depend on hosted Supabase.
- Frontend verification should include at least typecheck/build. Add heavier frontend test tooling only if needed by a later slice.
- Migration tests or review checks should verify RLS policies, constraints, indexes, trigger provisioning, and controlled tag constraints.

## Out of Scope

- Firebase, Auth0, Clerk, or any paid auth provider.
- Paid Supabase features.
- Password reset.
- Social login.
- Avatar upload or Supabase Storage.
- Account deletion UI.
- Realtime profile synchronization.
- Full host city, team, player, or match domain modeling beyond minimal FK targets and demo seeds.
- Exact user coordinates or raw check-in data.
- AI-generated profile or preference data.

## Further Notes

- Production should enable email confirmation. Development may disable confirmation to keep signup testing fast.
- Service role keys should not be exposed to the frontend and should not be required for normal profile APIs.
- `.env.example` should document Supabase URL, anon key, and JWKS URL without committing secrets.
- Future team/domain tickets can expand `host_cities` and `teams` while preserving the auth/profile relationships.
