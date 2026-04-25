from pathlib import Path

from scripts.edge_models.audio_fixture import generate_dummy_wave
from scripts.edge_models.manifest import (
  DOCS_DIR,
  MOBILE_MODELS_DIR,
  EdgeModelManifest,
  build_default_manifest,
)


def _render_candidate_table(manifest: EdgeModelManifest, task: str) -> str:
  lines = [
    '| Model | Accuracy | Latency | Footprint | ONNX | Mobile | Weighted | Verdict |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
  ]
  for candidate in [item for item in manifest.candidates if item.task == task]:
    verdict = 'Selected' if candidate.recommended else 'Fallback'
    lines.append(
      '| '
      f'{candidate.family} {candidate.variant} | '
      f'{candidate.scorecard.accuracy} | '
      f'{candidate.scorecard.latency} | '
      f'{candidate.scorecard.footprint} | '
      f'{candidate.scorecard.onnx_readiness} | '
      f'{candidate.scorecard.mobile_packaging} | '
      f'{candidate.scorecard.weighted_total()} | '
      f'{verdict} |'
    )
  return '\n'.join(lines)


def _render_edge_model_matrix(manifest: EdgeModelManifest) -> str:
  return f"""# Edge Model Matrix

This matrix uses engineering scores tuned for Graphite's constraints instead of
claiming reproduced benchmark numbers from this repo. The weighting prioritizes
mobile packaging, ONNX readiness, and reasonable accuracy under a small local
hardware budget.

## Constraints
- Target runtime: {manifest.constraints['target_runtime']}
- Hardware budget: {manifest.constraints['hardware_budget']}
- Storage budget: {manifest.constraints['storage_budget']}
- Integration policy: {manifest.constraints['integration_policy']}

## Selected defaults
- STT: `{manifest.selected_models['stt']}`
- TTS: `{manifest.selected_models['tts']}`

## STT candidates
{_render_candidate_table(manifest, 'stt')}

Why this choice:
- Whisper Tiny English remains the safest default for APK packaging because it
  is ONNX-friendly, compact, and already matches the current mobile placeholder
  copy.
- Whisper Base is the first upgrade path if accuracy matters more than startup cost.
- SenseVoice Small is attractive for multilingual work, but the export and
  mobile packaging path is less predictable for this repo today.

## TTS candidates
{_render_candidate_table(manifest, 'tts')}

Why this choice:
- Piper is already ONNX-native, CPU efficient, and well suited to reminder
  playback on mid-range phones.
- Coqui VITS and Kokoro can sound better in some cases, but they increase
  asset size and packaging risk.

## Validation metrics to track
""" + '\n'.join(f'- `{metric}`' for metric in manifest.validation_metrics) + """

## Export targets
- STT expected artifacts live under `mobile/models/stt/whisper-tiny-en-int8/`
- TTS expected artifacts live under `mobile/models/tts/piper-lessac-medium/`
- Use `mobile/models/manifest.json` as the source of truth for future downloads or exports.
"""


def _render_models_readme(manifest: EdgeModelManifest) -> str:
  return f"""# Mobile Models

This folder is the source of truth for local model packaging metadata.

## Selected defaults
- STT: `{manifest.selected_models['stt']}`
- TTS: `{manifest.selected_models['tts']}`

## Workflow
1. Generate or download the expected ONNX artifacts into the task-specific subdirectories.
2. Keep `manifest.json` aligned with any new model family or artifact path.
3. Use the dummy fixtures in `fixtures/` to smoke-test packaging and future inference glue.

## Current state
- The repo now contains model manifests, export plans, and dummy fixtures.
- Real ONNX weights are not bundled yet; drop them into the paths listed in
  `manifest.json` when ready.
"""


def _render_notebook_guide(manifest: EdgeModelManifest) -> str:
  return f"""# Notebook LLM Guide

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
- Recommended STT: `{manifest.selected_models['stt']}`
- Recommended TTS: `{manifest.selected_models['tts']}`
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
"""


def _render_profiling_notes() -> str:
  return """# Profiling

## Backend
- Use `python -m cProfile -o backend.prof backend/server.py` to sample route startup cost.
- Use `pytest -k backend_server --durations=5` to spot slow tests after backend changes.

## Model packaging
- Measure dummy asset generation and verification with
  `python -m cProfile -o edge_models.prof scripts/generate_edge_model_assets.py`.
- Once real ONNX files exist, track CPU real-time factor and memory with
  `onnxruntime` on representative mobile-class hardware.

## Metrics to preserve
- Backend route latency for `/api/health` and `/api/workflow/generate`
- WER and CER for STT
- TTS synthesis latency and output size
- APK asset footprint after bundling models
"""


def _write_text(path: Path, content: str) -> Path:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(content, encoding='utf-8')
  return path


def ensure_edge_workspace() -> list[Path]:
  manifest = build_default_manifest()
  created_paths: list[Path] = []

  for directory in [
    MOBILE_MODELS_DIR,
    MOBILE_MODELS_DIR / 'stt',
    MOBILE_MODELS_DIR / 'tts',
    MOBILE_MODELS_DIR / 'vision',
    MOBILE_MODELS_DIR / 'fixtures',
  ]:
    directory.mkdir(parents=True, exist_ok=True)

  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'manifest.json',
      manifest.model_dump_json(indent=2) + '\n',
    )
  )
  created_paths.append(
    _write_text(MOBILE_MODELS_DIR / 'README.md', _render_models_readme(manifest))
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'stt' / 'README.md',
      (
        'Place the selected STT ONNX artifacts under this directory as '
        'described in mobile/models/manifest.json.\n'
      ),
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'tts' / 'README.md',
      (
        'Place the selected TTS ONNX artifacts under this directory as '
        'described in mobile/models/manifest.json.\n'
      ),
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'vision' / 'README.md',
      (
        'Reserved for future on-device vision models. Keep this directory '
        'lightweight until mobile inference is implemented.\n'
      ),
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'stt' / 'EXPORT_PLAN.md',
      """# STT Export Plan

Recommended default: `stt-whisper-tiny-en-onnx-int8`

Suggested export command:
```bash
optimum-cli export onnx --model openai/whisper-tiny.en mobile/models/stt/whisper-tiny-en-int8
```

After export, quantize to int8 and keep the artifact paths aligned with
`mobile/models/manifest.json`.
""",
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'tts' / 'EXPORT_PLAN.md',
      """# TTS Export Plan

Recommended default: `tts-piper-lessac-medium`

Suggested workflow:
1. Download the Piper voice package for `en_US-lessac-medium`.
2. Place the ONNX file and metadata JSON under `mobile/models/tts/piper-lessac-medium/`.
3. Keep the filenames aligned with `mobile/models/manifest.json` for future APK bundling.
""",
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'fixtures' / 'dummy_transcript.txt',
      'Graphite will transcribe and summarize this offline meeting note.\n',
    )
  )
  created_paths.append(
    _write_text(
      MOBILE_MODELS_DIR / 'fixtures' / 'dummy_prompt.txt',
      'Remind me to review the fundraising workflow tonight.\n',
    )
  )
  created_paths.append(generate_dummy_wave(MOBILE_MODELS_DIR / 'fixtures' / 'dummy_audio.wav'))
  created_paths.append(
    _write_text(DOCS_DIR / 'EDGE_MODEL_MATRIX.md', _render_edge_model_matrix(manifest))
  )
  created_paths.append(
    _write_text(DOCS_DIR / 'NOTEBOOK_LLM_GUIDE.md', _render_notebook_guide(manifest))
  )
  created_paths.append(_write_text(DOCS_DIR / 'PROFILING.md', _render_profiling_notes()))

  return created_paths