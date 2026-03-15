# Phase 1 Mobile App Plan (Scaffold + Local SQLite)

## 1) Objectives
- Create a new Expo (React Native) project at **`/app/mobile`** without modifying **`/app/frontend`** or **`/app/backend`**.
- Establish a clean, future-ready folder structure for screens/components/services/config/db/utils/assets.
- Create **blank** local model directories:
  - `/app/mobile/models/tts`
  - `/app/mobile/models/stt`
  - `/app/mobile/models/vision`
- Install only the packages needed for Phase 1: **`expo-sqlite`** (plus minimal Expo web deps already included by default).
- Implement a local-first SQLite layer:
  - schema for **notes** and **workflows**
  - db initialization/migrations helper
  - typed-ish JS helpers (no UI usage yet)
- Stop after the database layer is implemented and runnable (no UI screens, no Supabase/Google/Gemini wiring).

## 2) Implementation Steps

### Phase 1A — Core POC: Local SQLite in Isolation
User stories (POC):
1. As a developer, I want a single function to initialize the local database so the app can boot reliably.
2. As a developer, I want to create a note record so I can prove local persistence works.
3. As a developer, I want to list notes ordered by updated time so I can confirm reads work.
4. As a developer, I want to create a workflow record so the second core entity is supported.
5. As a developer, I want a quick “smoke script” (invoked from app entry) that runs init → insert → read so regressions are obvious.

Steps:
- Create `/app/mobile` Expo app (JS template) with Expo web enabled.
- Add `expo-sqlite`.
- Add `/app/mobile/src/db/` with:
  - `db.js` (open db, run statements, transaction helpers)
  - `migrations.js` (versioned migrations + pragma `user_version`)
  - `schema.js` (SQL for tables/indexes)
  - `notesRepo.js` + `workflowsRepo.js` (CRUD helpers; minimal set: create/list/get/update/delete)
- Add a temporary dev-only entry hook (e.g., `src/utils/devSmokeTest.js`) that:
  - initializes db
  - inserts one note + one workflow
  - reads them back and logs to console
- Verify by running Expo web and confirming console output (no UI required beyond default screen).

### Phase 1B — App Scaffold + Folder Structure
User stories (scaffold):
1. As a developer, I want a predictable folder structure so future features can be added without churn.
2. As a developer, I want placeholder service/config modules so external integrations can be added later without refactors.
3. As a developer, I want blank model folders committed so edge models can be dropped in later.
4. As a developer, I want environment configuration conventions established so secrets can be added safely later.
5. As a developer, I want an app entry that cleanly boots and calls db init once.

Steps:
- Create directories (empty where appropriate):
  - `models/tts`, `models/stt`, `models/vision` (blank)
  - `src/app/` (entry glue for later)
  - `src/config/` (placeholder)
  - `src/db/` (from Phase 1A)
  - `src/services/` (placeholder)
  - `src/utils/` (dev smoke test)
  - `src/screens/` (placeholder)
  - `src/components/` (placeholder)
  - `src/assets/` (placeholder)
- Add minimal `src/config/constants.js` (app name, db name, schema version).
- Wire `App.js` to call db init on startup and optionally run the smoke test behind a flag.
- Add a short `mobile/README.md` describing how to run web and where the db layer lives.

### Phase 1C — Incremental Testing (No UI)
User stories (testing):
1. As a developer, I want deterministic migration behavior so schema upgrades don’t corrupt local data.
2. As a developer, I want database helpers to fail loudly with clear errors so issues are debuggable.
3. As a developer, I want id generation handled consistently so syncing later is feasible.
4. As a developer, I want timestamps stored consistently so sorting works.
5. As a developer, I want simple manual test steps to validate the POC quickly.

Steps:
- Run Expo web and validate:
  - first run: creates tables, inserts records, logs lists
  - second run: does not recreate tables; still reads persisted data
- Confirm tables:
  - `notes(id, title, content, created_at, updated_at)`
  - `workflows(id, title, prompt, graph_json, created_at, updated_at)` (graph_json nullable)
  - indexes on `updated_at`
- Ensure schema uses ISO timestamps and string UUIDs.

## 3) Next Actions
- After Phase 1 completion, pause for approval.
- With approval, proceed to Phase 2 (V1 UI foundation): navigation shell + placeholder screens, adhering to `/app/design_guidelines.md` and `data-testid` conventions.
- Later phases (separately approved): Supabase/Auth, markdown import/export, Google OAuth + background reminders, Gemini workflow agent + React Flow in WebView.

## 4) Success Criteria
- `/app/mobile` builds and runs on **Expo web** in this environment.
- Required blank model directories exist under `/app/mobile/models/*`.
- `src/` scaffold exists with the agreed structure.
- SQLite layer:
  - initializes via migrations
  - can create/list notes and workflows via repo helpers
  - persists across reloads
- No changes made to `/app/frontend` or `/app/backend`.
