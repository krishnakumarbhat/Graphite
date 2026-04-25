# Profiling

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
