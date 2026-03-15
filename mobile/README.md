# Second Brain Mobile Scaffold

This directory contains the new Expo-based mobile app scaffold for the V1 offline-first assistant.

## Phase 1 included
- Expo app initialized in `/app/mobile`
- Blank local model directories created:
  - `models/tts`
  - `models/stt`
  - `models/vision`
- SQLite database layer added under `src/db/`
  - `schema.js` for table/index definitions
  - `migrations.js` for schema versioning with `PRAGMA user_version`
  - `db.native.js` for the actual Expo SQLite runtime on iOS/Android
  - `db.web.js` as a scaffold-safe adapter so Expo web can compile in this environment
  - `notesRepo.js` and `workflowsRepo.js` for CRUD helpers
- App bootstrap wired through `src/core/bootstrap.js`
- Dev smoke test logs database readiness from `src/utils/devSmokeTest.js`

## Folder structure
- `src/core/` bootstrapping logic
- `src/config/` app constants + theme tokens
- `src/db/` SQLite schema, migrations, and repositories
- `src/services/` reserved for Supabase, Gemini, Google, sync services
- `src/utils/` helpers and dev smoke test
- `src/screens/` reserved for future mobile screens
- `src/components/` reserved for future reusable UI components
- `src/assets/` reserved for app-local assets
- `models/` reserved for on-device TTS/STT/Vision model files

## Run locally
```bash
cd /app/mobile
yarn web
```

## Notes
- Expo web is enabled for quick verification in this environment.
- `expo-sqlite` remains the primary local database layer for native iOS/Android.
- Because Expo web + `expo-sqlite` can require extra WASM configuration, the web build uses a no-op adapter while keeping the native SQLite schema/migration code fully ready for the next phase.
- Per the current phase scope, this scaffold intentionally stops before implementing UI screens, Supabase auth, Google OAuth, markdown import/export, or Gemini workflow generation.
