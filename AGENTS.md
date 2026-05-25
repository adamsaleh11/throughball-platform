# AGENTS.md — throughball-platform

# PURPOSE

This repo owns:
- frontend UI
- FastAPI operational backend
- deterministic scoring systems
- Supabase integration
- realtime systems
- retrieval persistence
- observability dashboards

This repo intentionally minimizes LLM dependence.

Backend logic should perform:
- ranking
- filtering
- aggregation
- recommendation scoring
- hotspot confidence calculation

before AI synthesis occurs.

---

# TECH STACK

Frontend:
- Next.js 15
- TypeScript
- Tailwind
- shadcn/ui
- React Query
- Zustand
- Mapbox GL

Backend:
- FastAPI
- Pydantic
- Redis
- Supabase

---

# ENGINEERING RULES

## Prefer deterministic logic first

The backend should compute:
- hotspot rankings
- venue scores
- itinerary ordering
- recommendation candidates

AI should explain results,
NOT invent them.

---

## Avoid unnecessary LLM calls

Do NOT:
- send giant contexts
- repeatedly regenerate summaries
- use AI for sorting/filtering

Use:
- backend scoring systems
- retrieval systems
- deterministic pipelines

---

## Privacy Rules

Never expose:
- exact user coordinates
- raw check-in data
- internal telemetry

Public APIs expose aggregate intelligence only.

---

## Observability

Every API must emit:
- request_id
- trace_id
- latency
- retries
- degraded execution

---

## Performance Goals

- low-latency APIs
- local-first development
- minimal cloud dependency
- small payloads

---

## Architecture Philosophy

This repo represents:
production-grade operational systems
with minimal AI cost.
