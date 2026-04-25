# Architecture

## Monorepo layout
- `backend/` — Flask service for status and workflow graph generation, plus static web serving.
- `frontend/` — React + CRACO web app.
- `mobile/` — Expo React Native app.
- `docs/` — project documentation.
- `scripts/` — Python tooling for model manifests, dummy fixtures, and validation.

## Product direction
- Web and mobile are separate apps with shared UX intent.
- Mobile is source-of-truth for on-device patterns.
- Web provides a routed desktop/tablet workspace with a dedicated `/notes` editor.

## High-level design
- Web app:
	- `/` hosts the agent dashboard, workflow canvas, memory search, and settings.
	- `/notes` hosts the local-first note editor with markdown import and AI drafting.
- Backend:
	- Flask serves both `/api/*` and the built SPA.
	- Notes persist to SQLite first via `backend/src/note_store.py`.
	- When Supabase is configured, notes are mirrored best-effort to remote tables.
- AI:
	- Workflow generation and AI note drafting use Gemini through the backend.
	- Vector memory still uses Pinecone when available.

## Design artifacts
- HLD draw.io: [graphite-system-hld.drawio](graphite-system-hld.drawio)
- Notes request flow draw.io: [graphite-notes-flow.drawio](graphite-notes-flow.drawio)
- Production note schema draft: [supabase_notes_schema.sql](supabase_notes_schema.sql)

## Data flow (current)
1. User enters workflow prompt.
2. Flask endpoint `/api/workflow/generate` calls Gemini.
3. Endpoint returns normalized graph JSON (`nodes`, `edges`).

## Notes flow (current)
1. User opens `/notes` in the web app.
2. The page requests `GET /api/notes?user_id=web-local`.
3. Flask reads and writes notes through the local SQLite store.
4. If Supabase is configured, the backend mirrors note rows and embedding payloads.
5. If Gemini is configured, `/api/notes/ai-draft` creates markdown note drafts.

## Web delivery (current)
1. Flask serves `/api/*` for backend routes.
2. Flask serves `frontend/build` for browser requests.
3. Mobile keeps using the same JSON contract at `http://127.0.0.1:8001/api/...`.
4. The web SPA uses React Router, so `/notes` resolves in the browser and through Flask fallback.

## Storage model
- Local development:
	- SQLite stores notes and serialized embedding payloads.
	- Browser local storage is used only as an offline fallback when the backend is down.
- Production target:
	- Supabase `notes` and `note_embeddings` tables receive mirrored note data.
	- The attached SQL file captures the schema expected for that mirror.
	- Direct remote DDL is not auto-applied here because the current environment exposes the
		Supabase REST client but not a direct Postgres admin connection.

## Security baseline
- API keys and secrets live in `.env` only.
- `.env.example` provides non-secret defaults.
- CORS defaults allow local dev origins only.
- Model manifests and dummy fixtures live under `mobile/models/` and contain no secrets.
