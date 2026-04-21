# Graphite

Local-first notes + workflows application built as a mobile-first Expo app with a FastAPI backend.

## Stack
- Mobile  + Web preview: React Native + Expo
- Local DB (mobile): expo-sqlite
- Cloud DB: Supabase (PostgreSQL + pgvector)
- Auth: Supabase Auth (email/password)
- Backend API: FastAPI + Uvicorn
- AI workflow engine: Gemini 1.5 Flash
- Local STT target: Whisper Tiny (placeholder wired in Note Editor)

## Monorepo layout
- `mobile/` — primary client (native + web preview)
- `backend/` — API and Gemini workflow generation
- `frontend/` — legacy web package (CRACO removed from scripts)
- `docs/` — architecture and contribution docs

## Quick start

### 1) Backend (localhost:8001)
```bash
cd backend
cp .env.example .env
pip3 install --user -r requirements.txt
python3 -m uvicorn --app-dir . server:app --reload --port 8001
```

Required in `backend/.env`:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)

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

## Open-source docs
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `RULES.md`
- `docs/ARCHITECTURE.md`
- `docs/UI_PARITY.md`
