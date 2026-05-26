# Plan: Supabase Auth Profile

> Source PRD: `docs/prds/supabase-auth-profile.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: Frontend exposes `/signup`, `/login`, `/onboarding`, and protected `/app/*`. Backend exposes protected profile routes under the profile API surface and does not proxy Supabase auth lifecycle routes.
- **Schema**: `profiles`, `user_preferences`, and `user_favorite_teams` are private user-owned tables. `host_cities` and `teams` are public reference tables if not already present.
- **Key models**: Profile identity is separate from preferences. Favorite teams are normalized through `user_favorite_teams`. Match tags remain a constrained text array.
- **Auth**: Next.js uses Supabase Auth directly. FastAPI validates Supabase bearer tokens and queries Supabase with the caller's token so RLS is exercised.
- **External services**: Hosted Supabase free tier is the only external dependency. No Firebase, Auth0, Clerk, service-role-dependent profile flow, or Dockerized local Supabase is required.

---

## Phase 1: Auth Schema Foundation

**User stories**: 2, 10, 11, 13, 14, 17

### What to build

Create the Supabase migration foundation that provisions profiles and preferences automatically, models favorite teams relationally, constrains controlled preference data, and enforces user isolation with RLS. Include minimal reference data only when needed for foreign-key targets and onboarding verification.

### Acceptance criteria

- [ ] A new Supabase auth user automatically receives one profile row and one preferences row.
- [ ] Users cannot read or mutate another user's profile, preferences, or favorite team rows through RLS.
- [ ] Favorite teams are represented by a join table with foreign keys to teams.
- [ ] Preferred match tags are constrained to the approved vocabulary.
- [ ] Constraints and indexes exist for profile names, avatar URLs, user preferences, and favorite team lookups.

---

## Phase 2: Backend Profile Contract

**User stories**: 12, 13, 14, 16, 17

### What to build

Add a protected FastAPI profile contract that validates Supabase bearer tokens, returns nested profile and preferences data, updates onboarding/profile data as one aggregate, computes `profile_completed`, and emits minimal observability metadata.

### Acceptance criteria

- [ ] Requests without a valid bearer token receive `401`.
- [ ] Authenticated users can fetch their own profile as `{ profile, preferences, meta }`.
- [ ] Authenticated users can update display name, avatar URL, home city, preferred tags, and favorite team IDs in one request.
- [ ] Profile completion is computed by the backend and cannot be directly user-forced.
- [ ] Profile responses include `request_id`, `trace_id`, and `degraded`.

---

## Phase 3: Frontend Auth Lifecycle

**User stories**: 1, 3, 4, 5, 17, 18

### What to build

Add Supabase-powered signup, login, logout, and session handling in the Next.js app. Keep token storage inside Supabase client behavior and avoid using Zustand for session lifecycle.

### Acceptance criteria

- [ ] A visitor can sign up with email, password, and optional display name.
- [ ] A returning user can log in.
- [ ] An authenticated user can log out.
- [ ] Frontend build/typecheck can run without real Supabase secrets.
- [ ] Dev email confirmation expectations and production hardening expectations are documented.

---

## Phase 4: Protected App And Onboarding

**User stories**: 5, 6, 7, 8, 9, 10, 11

### What to build

Create protected app routing and onboarding screens that read the backend profile contract, guide incomplete users through minimal setup, save profile/preferences/favorite teams, and route users based on `profile_completed`.

### Acceptance criteria

- [ ] Unauthenticated users visiting `/app/*` are redirected to login.
- [ ] Authenticated users with incomplete profiles are directed to onboarding.
- [ ] Onboarding can save display name, avatar URL, home city, favorite teams, and controlled match tags.
- [ ] Onboarding can be partial or skipped without breaking the app.
- [ ] Completed users land on the protected app surface.

---

## Phase 5: RLS Integration Proof

**User stories**: 13, 14, 15

### What to build

Add an opt-in Supabase-backed integration test that uses two real user sessions to prove tenant isolation across profiles, preferences, and favorite teams. Keep it gated by environment variables so local and CI runs without Supabase remain fast and reliable.

### Acceptance criteria

- [ ] The integration test is skipped when required Supabase test env vars are absent.
- [ ] With Supabase test env vars present, user A cannot read user B's private profile data.
- [ ] With Supabase test env vars present, user A cannot mutate user B's preferences or favorite team rows.
- [ ] The test documents the tenant-isolation behavior as an executable specification.
