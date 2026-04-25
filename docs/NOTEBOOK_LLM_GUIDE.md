# Notebook LLM Guide

Use this document as a compact project brief for future coding agents and notebooks.

## Product summary
- Graphite is a local-first notes and workflows product.
- Mobile in `mobile/` is the source-of-truth client.
- Flask in `backend/` serves both the API and the built web bundle.

## Active runtime contracts
- Mobile workflow generation depends on `POST /api/workflow/generate`.
- Backend health is available at `GET /api/health`.
- Built web assets are served from `frontend/build` by Flask.

## Voice model strategy
- Recommended STT: `stt-whisper-tiny-en-onnx-int8`
- Recommended TTS: `tts-piper-lessac-medium`
- Model metadata lives in `mobile/models/manifest.json`.
- Dummy fixtures live in `mobile/models/fixtures/`.

## Key run commands
- Backend: `cd backend && python3 server.py`
- Mobile web preview: `cd mobile && npm run web`
- Backend tests:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_backend_server.py`
- Model asset tests:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_edge_model_assets.py`

## Files to inspect first
- `backend/server.py`
- `backend/src/app_factory.py`
- `mobile/src/screens/note-editor-screen.js`
- `mobile/src/screens/profile-settings-screen.js`
- `mobile/models/manifest.json`

## Guardrails
- Keep mobile runtime behavior stable unless actual model loading is implemented end to end.
- Prefer Python tooling for manifest generation, validation, and export preparation.
- Do not treat dummy fixtures as production model verification; they only
  validate packaging expectations.
