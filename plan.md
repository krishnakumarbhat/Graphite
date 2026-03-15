# Phase 1 Mobile App Plan (Scaffold + Local SQLite)

## 1) Objectives
- ✅ Create a new Expo (React Native) project at **`/app/mobile`** without modifying **`/app/frontend`** or **`/app/backend`**.
- ✅ Establish a clean, future-ready folder structure for screens/components/services/config/db/utils/assets.
- ✅ Create **blank** local model directories:
  - `/app/mobile/models/tts`
  - `/app/mobile/models/stt`
  - `/app/mobile/models/vision`
- ✅ Install Phase 1 dependencies:
  - `expo-sqlite` (native SQLite runtime)
  - `react-dom` + `react-native-web` (added to enable Expo web verification)
- ✅ Implement a local-first SQLite layer:
  - schema for **notes** and **workflows**
  - db initialization/migrations helper
  - repository helpers (create/list/get/update/delete)
- ✅ Provide Expo web verification support in this environment **without** blocking native SQLite readiness.
- ✅ Stop after the database layer is implemented and runnable; pause for approval **before** building full UI screens and before any Supabase/Google/Gemini wiring.

**Phase 1 Status: COMPLETED**

## 2) Implementation Steps

### Phase 1A — Core POC: Local SQLite in Isolation
User stories (POC):
1. ✅ As a developer, I want a single function to initialize the local database so the app can boot reliably.
2. ✅ As a developer, I want to create a note record so I can prove local persistence works.
3. ✅ As a developer, I want to list notes ordered by updated time so I can confirm reads work.
4. ✅ As a developer, I want to create a workflow record so the second core entity is supported.
5. ✅ As a developer, I want a quick “smoke script” (invoked from app entry) that runs init → insert → read so regressions are obvious.

What was implemented:
- ✅ Expo project created at `/app/mobile` (JS).
- ✅ `expo-sqlite` added.
- ✅ Local SQLite layer created under `/app/mobile/src/db/`:
  - `schema.js` (tables + indexes)
  - `migrations.js` (versioned migrations using `PRAGMA user_version`)
  - `db.native.js` (real SQLite runtime using `expo-sqlite` for iOS/Android)
  - `notesRepo.js` + `workflowsRepo.js` (CRUD helpers)
- ✅ Dev-only smoke test added:
  - `src/utils/devSmokeTest.js` seeds sample note/workflow when empty and logs summary.

Important environment note (web verification):
- ✅ Added `src/db/db.web.js` as a **scaffold-safe adapter** so Expo web can compile in this environment while keeping native SQLite implementation intact.
  - Web mode intentionally reports `scaffold-only-web` and does not execute SQLite queries.


### Phase 1B — App Scaffold + Folder Structure
User stories (scaffold):
1. ✅ As a developer, I want a predictable folder structure so future features can be added without churn.
2. ✅ As a developer, I want placeholder service/config modules so external integrations can be added later without refactors.
3. ✅ As a developer, I want blank model folders committed so edge models can be dropped in later.
4. ✅ As a developer, I want environment configuration conventions established so secrets can be added safely later.
5. ✅ As a developer, I want an app entry that cleanly boots and calls db init once.

What was implemented:
- ✅ Directories created (empty where appropriate):
  - `models/tts`, `models/stt`, `models/vision` (blank)
  - `src/core/` (bootstrapping logic)
  - `src/config/` (constants + theme tokens)
  - `src/db/` (schema/migrations/repos + platform db adapters)
  - `src/services/` (placeholder)
  - `src/utils/` (id/time helpers + smoke test)
  - `src/screens/` (placeholder)
  - `src/components/` (placeholder)
  - `src/assets/` (placeholder)
- ✅ `src/config/constants.js` added (app name, db name, schema version, smoke-test flag).
- ✅ App bootstrap wired:
  - `src/core/bootstrap.js` initializes the db and runs smoke test when supported.
  - `App.js` calls bootstrap on startup and displays scaffold status.
- ✅ `mobile/README.md` added with how to run and a description of the db layer.

Implementation detail change vs original plan:
- `src/app/` was **renamed to `src/core/`** to avoid Expo Router auto-detection behavior associated with `src/app`.


### Phase 1C — Incremental Testing (No UI)
User stories (testing):
1. ✅ As a developer, I want deterministic migration behavior so schema upgrades don’t corrupt local data.
2. ✅ As a developer, I want database helpers to fail loudly with clear errors so issues are debuggable.
3. ✅ As a developer, I want id generation handled consistently so syncing later is feasible.
4. ✅ As a developer, I want timestamps stored consistently so sorting works.
5. ✅ As a developer, I want simple manual test steps to validate the POC quickly.

Verification completed:
- ✅ Lint passed on `/app/mobile` JS sources.
- ✅ Testing agent report: 100% frontend success.
- ✅ `yarn expo export --platform web` succeeds.
- ✅ Screenshot verification confirmed the scaffold renders in web mode and shows the expected **scaffold-only warning**.

Database schema confirmed:
- ✅ `notes(id, title, content, created_at, updated_at, source_path)`
  - index: `idx_notes_updated_at`
- ✅ `workflows(id, title, prompt, graph_json, created_at, updated_at)`
  - index: `idx_workflows_updated_at`
- ✅ ISO timestamps + UUID strings.

## 3) Next Actions
- ⏸️ Pause for approval (as requested) before any UI work beyond the current bootstrap display.
- Upon approval, proceed to **Phase 2 (V1 UI foundation)**:
  - Navigation shell + placeholder screens (Notes, Editor, Workflow Agent, Settings)
  - Adhere to `/app/design_guidelines.md`
  - Ensure `data-testid` on all interactive/key informational elements
  - Keep components in **.js**
- Later phases (separately approved):
  - Supabase/Auth + sync
  - Markdown import/export with `expo-file-system`
  - Google OAuth + background reminders scaffolding
  - Gemini workflow agent + React Flow in WebView

## 4) Success Criteria
- ✅ `/app/mobile` builds and can be verified via **Expo web** in this environment.
- ✅ Required blank model directories exist under `/app/mobile/models/*`.
- ✅ `src/` scaffold exists with the agreed structure.
- ✅ SQLite layer implemented for native iOS/Android:
  - initializes via migrations
  - can create/list notes and workflows via repo helpers
- ✅ Web verification does not block compilation:
  - `db.web.js` provides a scaffold-safe adapter
- ✅ No changes made to `/app/frontend` or `/app/backend`.