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
  - `react-dom` + `react-native-web` (to enable Expo web verification)
- ✅ Implement a local-first SQLite layer:
  - schema for **notes** and **workflows**
  - db initialization/migrations helper
  - repository helpers (create/list/get/update/delete)
- ✅ Provide Expo web verification support in this environment **without** blocking native SQLite readiness.
- ✅ Stop after the database layer is implemented and runnable; pause for approval **before** building full UI and before any Supabase/Google/Gemini wiring.

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
  - `src/utils/devSmokeTest.js`

Important environment note (web verification):
- ✅ Added `src/db/db.web.js` as a **scaffold-safe adapter** so Expo web can compile in this environment while keeping native SQLite implementation intact.
  - Web mode intentionally reports scaffold-only status and does not execute SQLite queries.

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
- ✅ `mobile/README.md` added.

Implementation detail change vs original plan:
- ✅ Avoided `src/app/` naming to prevent Expo Router auto-detection; kept boot logic in `src/core/`.

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
- ✅ Screenshot verification confirmed the scaffold renders in web mode.

Database schema confirmed:
- ✅ `notes(id, title, content, created_at, updated_at, source_path)`
  - index: `idx_notes_updated_at`
- ✅ `workflows(id, title, prompt, graph_json, created_at, updated_at)`
  - index: `idx_workflows_updated_at`
- ✅ ISO timestamps + UUID strings.

---

# Phase 2 Mobile App Plan (UI Foundation + Preview Visibility Fix)

## 1) Objectives
- ✅ Proceed to Phase 2 (approved by user).
- ✅ Build the **V1 UI foundation** in `/app/mobile` (React Native / Expo), following `/app/design_guidelines.md`:
  - calm premium look (teal + warm neutrals)
  - no purple
  - left-aligned editorial rhythm
  - `data-testid` on all interactive elements + key informational text
  - components remain in **.js**
- ✅ Add navigation and Phase-2 screens in `/app/mobile` (no Supabase/Google/Gemini/File import-export implementation yet; placeholders only):
  - Notes List
  - Note Editor (basic editor; block editor architecture placeholder)
  - Workflow Agent (prompt + placeholder canvas)
  - Settings
- ✅ Fix the user-visible preview:
  - The environment preview URL currently shows the old `/app/frontend` placeholder (“Building something incredible ~!”).
  - **User selected Option A:** mirror a faithful web preview shell in `/app/frontend` so the fixed preview URL shows the app.
- ⛔ Continue to avoid implementing Supabase, Google OAuth, Gemini API calls, and markdown import/export in this phase (placeholders only).

**Phase 2 Status: APPROVED / IN PROGRESS (not yet implemented)**

## 2) Implementation Steps

### Phase 2A — Preview Visibility Strategy (Option A: Web Mirror in `/app/frontend`)
User stories:
1. As a user, I want the **preview URL** to show the app we’re working on.
2. As a developer, I want primary mobile development to remain in `/app/mobile`.

Steps:
- Replace the placeholder screen in `/app/frontend` with a **Mobile Preview** web app that mirrors the Phase 2 screens:
  - Notes
  - Note Editor
  - Workflow Agent
  - Settings
- Keep the web mirror intentionally thin:
  - UI-only and/or mocked local data (no Supabase/Google/Gemini)
  - Reuse existing shadcn components from `/app/frontend/src/components/ui`.
  - Match the mobile design guidelines (teal + warm neutrals; no gradients on reading surfaces).
- Add `data-testid` attributes to all interactive elements and key informational text in the web mirror.

Deliverables:
- Preview URL renders the mirrored app instead of “Building something incredible ~!”.

### Phase 2B — Navigation Shell (Mobile)
User stories:
1. As a user, I can move between Notes, Workflow Agent, and Settings.
2. As a user, I can open a Note Editor from Notes.

Steps:
- Add navigation (React Navigation recommended for Phase 2).
- Implement bottom tabs:
  - Notes
  - Workflow
  - Settings
- Implement stack navigation for Notes → Note Editor.
- Add required `testID` / `data-testid` mappings:
  - `tab-notes`, `tab-workflow`, `tab-settings`
  - screen titles and primary actions.

### Phase 2C — Notes UI (Mobile)
User stories:
1. As a user, I can see a list of notes.
2. As a user, I can create a note.
3. As a user, I can open a note.

Steps:
- Notes List screen:
  - header title + create button
  - list rendering
  - empty state
- Wire to local repo on native (SQLite) via existing `notesRepo.js`.
- For Expo web inside `/app/mobile`, continue to use the current scaffold adapter behavior (no real persistence), but UI should still render.

Test IDs:
- `notes-create-button`
- `notes-list-item`
- `notes-empty-state`

### Phase 2D — Note Editor (Mobile)
User stories:
1. As a user, I can edit a note title and content.
2. As a developer, the architecture can evolve into a Notion-like block editor later.

Steps:
- Implement basic editor:
  - Title input
  - Content input (single TextInput for now)
  - Save/back behavior that updates `updated_at`
- Add a placeholder for future block-based editor modules (directory + interface sketch), without implementing full block operations yet.

Test IDs:
- `editor-title-input`
- `editor-content-input`
- `editor-save-button`

### Phase 2E — Workflow Agent Screen Placeholder (Mobile)
User stories:
1. As a user, I can type a prompt.
2. As a user, I can press Generate.
3. As a user, I see a placeholder canvas area for the graph.

Steps:
- Build screen:
  - prompt input
  - generate button (placeholder handler)
  - canvas placeholder container

Test IDs:
- `workflow-prompt-input`
- `workflow-generate-button`
- `workflow-canvas-placeholder`

### Phase 2F — Settings Screen Placeholder (Mobile)
User stories:
1. As a user, I see grouped sections for Account/Sync/Integrations/Storage.

Steps:
- Build settings screen with grouped cards.
- Add placeholders for:
  - Supabase Auth (later)
  - Sync status (later)
  - Google integrations (later)

Test IDs:
- `settings-list`

### Phase 2G — Web Mirror Implementation in `/app/frontend` (Faithful Preview)
User stories:
1. As a user, I can view and click through all Phase 2 screens in the preview URL.
2. As a developer, the preview clearly communicates “this is the mirrored web preview of mobile.”

Steps:
- Implement a simple web navigation layout in `/app/frontend` (left nav or top tabs) for:
  - Notes
  - Workflow
  - Settings
- Implement a Note Editor route/screen.
- Use shadcn components for consistency.
- Mirror the same `data-testid` IDs as mobile where possible.

### Phase 2H — Testing & Verification
User stories:
1. As a user, I can finally see the app in the fixed preview URL.
2. As a developer, builds pass.

Steps:
- Verify `/app/mobile`:
  - `yarn expo export --platform web` passes
  - navigation renders without runtime errors
- Verify `/app/frontend`:
  - `yarn start` (or environment’s preview runner) loads mirrored UI
  - preview shows Notes/Editor/Workflow/Settings
- Add screenshots for:
  - Notes list
  - Note editor
  - Workflow agent placeholder
  - Settings

## 3) Next Actions
- After Phase 2 is implemented and approved:
  - Phase 3: Supabase Auth + sync mock
  - Phase 4: Markdown import/export with `expo-file-system`
  - Phase 5: Google OAuth scaffolding + background reminder placeholder
  - Phase 6: Gemini workflow JSON + React Flow in WebView

## 4) Success Criteria
- `/app/mobile`:
  - Has working navigation and all Phase 2 screens (Notes, Note Editor, Workflow Agent placeholder, Settings).
  - Adheres to `/app/design_guidelines.md` and uses consistent `data-testid`.
- `/app/frontend`:
  - Preview URL shows the mirrored app UI (replacing “Building something incredible ~!”).
  - Mirrors the same information architecture and major test IDs.
- No breakage to `/app/backend`.
- No external integrations implemented yet beyond placeholders.
