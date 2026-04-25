# Mobile Models

This folder is the source of truth for local model packaging metadata.

## Selected defaults
- STT: `stt-whisper-tiny-en-onnx-int8`
- TTS: `tts-piper-lessac-medium`

## Workflow
1. Generate or download the expected ONNX artifacts into the task-specific subdirectories.
2. Keep `manifest.json` aligned with any new model family or artifact path.
3. Use the dummy fixtures in `fixtures/` to smoke-test packaging and future inference glue.

## Current state
- The repo now contains model manifests, export plans, and dummy fixtures.
- Real ONNX weights are not bundled yet; drop them into the paths listed in
  `manifest.json` when ready.
