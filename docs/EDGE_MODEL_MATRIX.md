# Edge Model Matrix

This matrix uses engineering scores tuned for Graphite's constraints instead of
claiming reproduced benchmark numbers from this repo. The weighting prioritizes
mobile packaging, ONNX readiness, and reasonable accuracy under a small local
hardware budget.

## Constraints
- Target runtime: Android APK with on-device inference
- Hardware budget: 4 GB RTX 3050 and CPU fallback
- Storage budget: keep model payloads compact
- Integration policy: prefer ONNX-native or ONNX-exportable models with low mobile risk

## Selected defaults
- STT: `stt-whisper-tiny-en-onnx-int8`
- TTS: `tts-piper-lessac-medium`

## STT candidates
| Model | Accuracy | Latency | Footprint | ONNX | Mobile | Weighted | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Whisper tiny.en | 7 | 9 | 9 | 10 | 9 | 8.45 | Selected |
| Whisper base.en | 8 | 7 | 7 | 10 | 7 | 7.8 | Fallback |
| SenseVoice small | 9 | 8 | 6 | 7 | 6 | 7.6 | Fallback |

Why this choice:
- Whisper Tiny English remains the safest default for APK packaging because it
  is ONNX-friendly, compact, and already matches the current mobile placeholder
  copy.
- Whisper Base is the first upgrade path if accuracy matters more than startup cost.
- SenseVoice Small is attractive for multilingual work, but the export and
  mobile packaging path is less predictable for this repo today.

## TTS candidates
| Model | Accuracy | Latency | Footprint | ONNX | Mobile | Weighted | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Piper en_US-lessac-medium | 8 | 9 | 8 | 10 | 10 | 8.8 | Selected |
| Coqui VITS ljspeech | 8 | 7 | 6 | 7 | 6 | 7.05 | Fallback |
| Kokoro 82M | 9 | 6 | 5 | 6 | 5 | 6.75 | Fallback |

Why this choice:
- Piper is already ONNX-native, CPU efficient, and well suited to reminder
  playback on mid-range phones.
- Coqui VITS and Kokoro can sound better in some cases, but they increase
  asset size and packaging risk.

## Validation metrics to track
- `WER`
- `CER`
- `real_time_factor`
- `peak_memory_mb`
- `apk_asset_size_mb`

## Export targets
- STT expected artifacts live under `mobile/models/stt/whisper-tiny-en-int8/`
- TTS expected artifacts live under `mobile/models/tts/piper-lessac-medium/`
- Use `mobile/models/manifest.json` as the source of truth for future downloads or exports.
