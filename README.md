# Graphite

Local-first notes + workflows application built as a mobile-first Expo app with a Flask backend.

## Stack
- Mobile  + Web preview: React Native + Expo
- Local DB (mobile): expo-sqlite
- Cloud DB: Supabase (PostgreSQL + pgvector)
- Auth: Supabase Auth (email/password)
- Backend API: Flask
- AI workflow engine: Gemini 3.5 Flash with 3.1 Flash fallback
- Local STT target: Whisper Tiny (placeholder wired in Note Editor)

## Monorepo layout
- `mobile/` — primary client (native + web preview)
- `backend/` — Flask API, Gemini workflow generation, and static web serving
- `frontend/` — legacy web package (CRACO removed from scripts)
- `docs/` — architecture and contribution docs
- `scripts/` — Python tooling for model manifests, dummy fixtures, and validation

## Quick start

### 1) Backend (localhost:8001)
```bash
cp .env.example .env

cd backend
pip3 install --user -r requirements.txt
python3 server.py
```

Preferred local setup:
- Use the repo-root `.env` created from `.env.example`.
- `backend/.env` is still supported for legacy local setups.
- `.env` and `backend/.env` are gitignored and should never be committed.

Required for the root `.env` example:
- `superbase_api`
- `superbase_pub_key`
- `gemini_api`

Optional for backend writes to Supabase:
- `superbase_secret_key`

### 2) Mobile app + web preview (localhost:8081)
Set env vars in your shell:
```bash
export EXPO_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export EXPO_PUBLIC_SUPABASE_ANON_KEY="your_anon_key"
export EXPO_PUBLIC_API_URL="http://127.0.0.1:8001"
```

Run:
```bash
cd mobile
npm install
npm run web
```

## USB Android localhost access
If your phone is connected by USB and must use localhost:
```bash
adb devices
adb reverse tcp:8081 tcp:8081
adb reverse tcp:8001 tcp:8001
```

On phone:
- Expo web preview: `http://127.0.0.1:8081`
- Backend health: `http://127.0.0.1:8001/api/health`

## UI behavior
- Top navigation: `Notes`, `Workflows`
- Top-right profile icon: opens `Profile & Settings`
- Profile screen: Login / Registration with Supabase Auth
- Local data isolation: SQLite `notes` and `workflows` are scoped by `user_id`
- Voice Note button in editor inserts a local STT placeholder block

## SQLite schema highlights
- `users` table (local mirror)
- `notes.user_id` foreign key -> `users.id`
- `workflows.user_id` foreign key -> `users.id`

## APK build (downloadable)
Using EAS Build:
```bash
cd mobile
npm install -g eas-cli
eas login
eas build:configure
eas build -p android --profile preview
```

After build finishes, download APK from the EAS build URL.

## Local model folders
Store your local models under:
- `mobile/models/tts`
- `mobile/models/stt`
- `mobile/models/vision`

Bootstrap the edge-model workspace and dummy fixtures:
```bash
.venv/bin/python scripts/generate_edge_model_assets.py
```

Validate the backend and model workspace:
```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_backend_server.py tests/test_edge_model_assets.py
```

## Docker and Render

Build the image:
```bash
docker build -t graphite .
```

Run it locally against your existing Supabase project:
```bash
docker run --rm -p 8001:8001 --env-file backend/.env graphite
```

Render setup notes:
- Deploy from the repo root with the included `Dockerfile`.
- Set `SUPABASE_URL` plus either `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_PUBLIC_KEY`.
- Set `GEMINI_API_KEY` and keep `GEMINI_MODEL=gemini-3.5-flash` with `GEMINI_FALLBACK_MODEL=gemini-3.1-flash`.
- Leave `GRAPHITE_MODEL_REPO` on `krishnah27/graphite` unless you move the Hugging Face artifacts.
- Render provides `PORT`; the container already binds to it.

## Open-source docs
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `RULES.md`
- `docs/ARCHITECTURE.md`
- `docs/UI_PARITY.md`
- `docs/EDGE_MODEL_MATRIX.md`
- `docs/NOTEBOOK_LLM_GUIDE.md`
- `docs/PROFILING.md`
