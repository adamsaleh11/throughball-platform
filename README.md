# throughball-platform

Platform repo for local-first demo development.

## Scope

- Frontend UI
- FastAPI operational backend
- Deterministic scoring systems
- Supabase integration
- Realtime systems
- Retrieval persistence
- Observability dashboards

## Development Principles

- Keep local development as the default.
- Do not add paid SaaS tools by default.
- Do not add hosted observability tools by default.
- Do not add always-on infrastructure.
- Deploy to cloud only when needed for the demo.

## Getting Started

```sh
cp .env.example .env.local
```

## Local Development

Install frontend dependencies:

```sh
npm install
```

Install backend dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

Run the Next.js frontend:

```sh
npm run dev:web
```

Run the FastAPI backend:

```sh
npm run dev:api
```

Check backend health:

```sh
curl http://localhost:8000/health
```

No cloud resources, hosted Redis, paid monitoring, Vertex AI calls, or external APIs are required for this foundation ticket.
