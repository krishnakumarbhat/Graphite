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
  - `src/screens/` (placeholder at Phase 1; populated in Phase 2)
  - `src/components/` (placeholder at Phase 1; populated in Phase 2)
  - `src/assets/` (placeholder)
- ✅ `src/config/constants.js` added (app name, db name, schema version, smoke-test flag).
- ✅ App bootstrap wired:
  - `src/core/bootstrap.js` initializes the db and runs smoke test when supported.
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
  - `data-testid` / `testID` coverage on interactive elements and key informational text
  - components remain in **.js**
- ✅ Add Phase-2 screens in `/app/mobile` (placeholders only; no Supabase/Google/Gemini/File import-export implementation yet):
  - Notes List
  - Note Editor (basic editor; block editor architecture placeholder)
  - Workflow Agent (prompt + placeholder canvas)
  - Settings
- ✅ Fix the user-visible preview:
  - The environment preview URL previously showed the old `/app/frontend` placeholder (“Building something incredible ~!”).
  - **Option A implemented:** mirror a faithful web preview shell in `/app/frontend` so the fixed preview URL shows the app.
- ✅ Ensure light/dark support in the preview mirror and align tokens to the approved design system.
- ⛔ Continue to avoid implementing Supabase, Google OAuth, Gemini API calls, and markdown import/export in this phase (placeholders only).

**Phase 2 Status: COMPLETED**

## 2) Implementation Steps

### Phase 2A — Preview Visibility Strategy (Option A: Web Mirror in `/app/frontend`)
User stories:
1. ✅ As a user, I want the **preview URL** to show the app we’re working on.
2. ✅ As a developer, I want primary mobile development to remain in `/app/mobile`.

What was implemented:
- ✅ Replaced the placeholder screen in `/app/frontend` with a **Mirrored Mobile Preview** web app.
- ✅ Mirrored key Phase 2 flows:
  - Notes list + search
  - Note editor open/back/save
  - Workflow agent prompt + generate placeholder
  - Settings toggles + model folder visibility
- ✅ Added theme support:
  - `/app/frontend/src/index.css` updated to teal + warm-neutral shadcn tokens (light/dark)
  - `ThemeProvider` wired in `/app/frontend/src/index.js`
- ✅ Added `data-testid` to major interactive and key informational elements.

Deliverables:
- ✅ Preview URL now renders the app mirror instead of “Building something incredible ~!”.

### Phase 2B — Navigation Shell (Mobile)
User stories:
1. ✅ As a user, I can move between Notes, Workflow Agent, and Settings.
2. ✅ As a user, I can open a Note Editor from Notes.

What was implemented (adjusted vs original plan):
- ✅ Implemented a simple in-app tab state navigation (instead of adding React Navigation) to reduce dependency churn.
- ✅ Bottom tab bar component:
  - `src/components/bottom-tab-bar.js`
- ✅ Editor is presented as an in-app state (notes → editor) and hides the tab bar while editing.

Test IDs:
- ✅ `tab-notes`, `tab-workflow`, `tab-settings`
- ✅ `notes-screen`, `workflow-screen`, `settings-screen`, `note-editor-screen`

### Phase 2C — Notes UI (Mobile)
User stories:
1. ✅ As a user, I can see a list of notes.
2. ✅ As a user, I can create a note.
3. ✅ As a user, I can open a note.

What was implemented:
- ✅ Notes list screen:
  - `src/screens/notes-screen.js`
  - create button
  - search input
  - list items with metadata
  - empty state
- ✅ Data strategy:
  - Native (when SQLite available): load from repo helpers
  - Web (Expo web): graceful fallback to seeded preview data
  - Implemented via `src/services/localDataService.js` + `src/data/previewData.js`

Test IDs:
- ✅ `notes-create-button`
- ✅ `notes-search-input`
- ✅ `notes-empty-state`
- ✅ `notes-list-item-<id>`

### Phase 2D — Note Editor (Mobile)
User stories:
1. ✅ As a user, I can edit a note title and content.
2. ✅ As a developer, the architecture can evolve into a Notion-like block editor later.

What was implemented:
- ✅ Basic editor screen:
  - `src/screens/note-editor-screen.js`
  - title + content inputs
  - save/back controls
  - block-type chips as an explicit “placeholder” affordance
- ✅ Save behavior:
  - Native: uses repos via `localDataService.saveNoteForApp()`
  - Web: local fallback note updates

Test IDs:
- ✅ `editor-title-input`
- ✅ `editor-content-input`
- ✅ `editor-save-button`
- ✅ `editor-back-button`

### Phase 2E — Workflow Agent Screen Placeholder (Mobile)
User stories:
1. ✅ As a user, I can type a prompt.
2. ✅ As a user, I can press Generate.
3. ✅ As a user, I see a placeholder canvas area for the graph.

What was implemented:
- ✅ Workflow screen:
  - `src/screens/workflow-screen.js`
  - prompt input
  - generate button
  - placeholder “node cards” that update from the prompt (no Gemini yet)
- ✅ Placeholder graph generation:
  - `localDataService.buildWorkflowPreview()`

Test IDs:
- ✅ `workflow-prompt-input`
- ✅ `workflow-generate-button`
- ✅ `workflow-canvas-placeholder`
- ✅ `workflow-node-<id>`

### Phase 2F — Settings Screen Placeholder (Mobile)
User stories:
1. ✅ As a user, I see grouped sections for Account/Sync/Integrations/Storage.

What was implemented:
- ✅ Settings screen:
  - `src/screens/settings-screen.js`
  - theme toggle
  - reminder toggle placeholders
  - offline-first toggle
  - model directory visibility
  - runtime status copy (including web SQLite caveat)

Test IDs:
- ✅ `settings-list`
- ✅ `settings-theme-toggle-button`
- ✅ `settings-speak-reminders-switch`
- ✅ `settings-offline-priority-switch`

### Phase 2G — Web Mirror Implementation in `/app/frontend` (Faithful Preview)
User stories:
1. ✅ As a user, I can view and click through all Phase 2 screens in the preview URL.
2. ✅ As a developer, the preview clearly communicates “this is the mirrored web preview of mobile.”

What was implemented:
- ✅ Web mirror shell implemented at:
  - `src/components/preview/app-preview-shell.jsx`
  - `src/components/preview/preview-data.js`
- ✅ Web mirror uses shadcn components:
  - Button, Card, Tabs, Input, Textarea, ScrollArea, Switch, Badge, Separator, Sonner
- ✅ Light/dark theme toggle works (via `next-themes`).
- ✅ Model folders are displayed.

### Phase 2H — Testing & Verification
User stories:
1. ✅ As a user, I can finally see the app in the fixed preview URL.
2. ✅ As a developer, builds pass.

Verification completed:
- ✅ `/app/mobile`:
  - `yarn expo export --platform web` passes
  - JS lint passes
- ✅ `/app/frontend`:
  - `yarn build` passes
  - JS lint passes
- ✅ Visual verification:
  - Screenshots captured for: home/notes, editor, workflow, settings, dark mode.
- ✅ Testing agent iteration 2:
  - Reported all core requirements passing.
  - Noted a low-priority point about some mobile-specific test IDs due to mirror structure; confirmed relevant selectors exist in the corresponding interaction states.
- ✅ Cleanup:
  - Removed temporary `/app/backend_test.py` created during testing.

## 3) Next Actions
- Phase 3: **Supabase Auth + Sync Mock**
  - add supabase client module
  - email/password auth screens (or settings section)
  - mock push/pull sync pipeline between SQLite and Supabase
- Phase 4: **Markdown Import/Export**
  - `expo-file-system` utilities
  - import `.md` into SQLite notes, export notes to `.md`
- Phase 5: **Google OAuth Scaffolding + Background Reminder Placeholder**
  - calendar/docs scopes scaffolding
  - background task placeholder
  - local TTS reminder placeholder integration
- Phase 6: **Gemini Workflow JSON + React Flow in WebView**
  - service function for strictly formatted nodes/edges JSON
  - WebView-based React Flow canvas

## 4) Success Criteria
- ✅ `/app/mobile`:
  - Has Notes, Note Editor, Workflow Agent placeholder, Settings.
  - Uses teal + warm neutrals, no purple.
  - Provides graceful fallback preview data when SQLite is unavailable on web.
  - Includes consistent `testID` coverage.
- ✅ `/app/frontend`:
  - Preview URL shows the mirrored app UI (no longer the placeholder).
  - Supports notes/editor/workflow/settings + theme toggle.
  - Uses approved design tokens and avoids disallowed gradients.
- ✅ No breakage to `/app/backend`.
- ✅ No external integrations implemented yet beyond placeholders.
