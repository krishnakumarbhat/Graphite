# Contributing to Graphite

Graphite has three actively used surfaces:

- `backend/`: Flask API, SQLite note storage, Gemini orchestration, research endpoints.
- `frontend/`: React web app served from the backend build output.
- `mobile/`: React Native / Expo client for mobile and web preview.

## Local setup
1. Clone the repo and create the backend environment.
   - `cd backend`
   - `python3 -m venv ../.venv`
   - `../.venv/bin/pip install -r requirements.txt`
2. Install frontend dependencies.
   - `cd ../frontend`
   - `npm install`
3. Install mobile dependencies if you are touching the mobile app.
   - `cd ../mobile`
   - `npm install`

## Running the project
1. Start the backend from the repository root.
   - `env GRAPHITE_PORT=8002 .venv/bin/python backend/server.py`
2. Start the frontend dev server if you are iterating on the web app directly.
   - `cd frontend`
   - `npm start`
3. Build the frontend when you want Flask to serve the latest UI.
   - `cd frontend`
   - `npm run build`
4. Start the mobile preview when needed.
   - `cd mobile`
   - `npm run web`

## Environment notes
- Backend `.env` values are loaded from both `backend/.env` and the repository root `.env`.
- Root aliases such as `gemini_api` and `superbase_pub_key` are supported.
- Frontend auth uses `frontend/.env.local` with `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY`.
- SQLite remains the source of truth for note persistence. Supabase-backed auth is optional.

## Contribution workflow
1. Create a focused branch such as `feat/<topic>`, `fix/<topic>`, or `docs/<topic>`.
2. Keep changes narrow and update the relevant docs when behavior changes.
3. Include screenshots or short recordings for visible UI changes.
4. Mention any manual verification you ran in the PR description.

## Engineering expectations
- Do not commit secrets, tokens, or `.env` files with real credentials.
- Keep web and mobile experiences aligned where the product surface overlaps.
- Prefer root-cause fixes over UI-only patches.
- Add or update tests for backend logic when changing persistence, orchestration, or request validation.
- Avoid unrelated refactors in the same PR.

## Validation checklist
- Backend imports cleanly and starts without tracebacks.
- `frontend npm run build` passes for web UI changes.
- New routes or endpoints are exercised at least once manually.
- Note-saving changes are tested for both guest and signed-in flows when applicable.

## Commit style
Use Conventional Commits when practical:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

## Security reporting
Do not open public issues for vulnerabilities.
See `SECURITY.md` for the disclosure process.
