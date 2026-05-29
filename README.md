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

Run the full local stack:

```sh
npm run dev
```

Install backend dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps/api/requirements.txt
```

Run the Next.js frontend:

```sh
npm run dev:web
```

Run the FastAPI backend:

```sh
npm run dev:api
```

On Windows PowerShell:

```powershell
npm run dev:api:win
```

Check backend health:

```sh
curl http://localhost:8000/health
```

No cloud resources, hosted Redis, paid monitoring, Vertex AI calls, or external APIs are required for this foundation ticket.

## World Cup Fixture Import

Runtime match APIs read Supabase only. To refresh World Cup fixture seed data manually from API-Football, run:

```sh
API_FOOTBALL_KEY=... python3 scripts/import_api_football_worldcup.py
```

The script emits SQL to `supabase/generated/api-football-worldcup.sql`, which is gitignored because provider-derived data should not be committed without a licensing review. Apply the generated SQL through your local Supabase SQL workflow after reviewing it.

You can also render SQL from a saved provider response without using network quota:

```sh
python3 scripts/import_api_football_worldcup.py --input-json provider-fixtures.json
```
