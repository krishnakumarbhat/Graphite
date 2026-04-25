# Graphite Mobile (Expo)

Local-first mobile app with Expo + React Native and web preview support.

## Current architecture
- Top navigation: `Notes` + `Workflows`
- Profile icon (top-right): opens `Profile & Settings`
- Auth: Supabase email/password login + registration
- Local DB: `expo-sqlite` with `users`, `notes`, `workflows`
- Data isolation: notes/workflows are scoped by `user_id`
- AI workflow generation: backend Flask endpoint with Gemini 1.5 Flash
- Voice Note: placeholder block in Note Editor for local Whisper Tiny integration

## Environment
Set Expo public env vars before starting:
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- `EXPO_PUBLIC_API_URL` (default `http://127.0.0.1:8001`)

## Run
```bash
cd mobile
npm install
npm run web
```

## Android USB (for localhost)
```bash
adb devices
adb reverse tcp:8081 tcp:8081
adb reverse tcp:8001 tcp:8001
```

Then use phone browser / webview with:
- `http://127.0.0.1:8081` (Expo web)
- `http://127.0.0.1:8001/api/health` (backend health)

## Local model directories
- `models/tts`
- `models/stt`
- `models/vision`

Generate the shared model manifest and dummy fixtures from the repo root:
```bash
.venv/bin/python scripts/generate_edge_model_assets.py
```

The generated manifest lives at `mobile/models/manifest.json` and tracks the recommended ONNX-ready STT/TTS candidates.
