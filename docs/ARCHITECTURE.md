# Architecture

## Monorepo layout
- `backend/` — FastAPI service for status and workflow graph generation.
- `frontend/` — React + CRACO web app.
- `mobile/` — Expo React Native app.
- `docs/` — project documentation.

## Product direction
- Web and mobile are separate apps with shared UX intent.
- Mobile is source-of-truth for on-device patterns.
- Web provides responsive desktop/tablet workspace with the same information architecture.

## Data flow (current)
1. User enters workflow prompt.
2. Backend endpoint `/api/workflow/generate` calls Gemini.
3. Endpoint returns normalized graph JSON (`nodes`, `edges`).

## Security baseline
- API keys and secrets live in `.env` only.
- `.env.example` provides non-secret defaults.
- CORS defaults allow local dev origins only.
