# STT Export Plan

Recommended default: `stt-whisper-tiny-en-onnx-int8`

Suggested export command:
```bash
optimum-cli export onnx --model openai/whisper-tiny.en mobile/models/stt/whisper-tiny-en-int8
```

After export, quantize to int8 and keep the artifact paths aligned with
`mobile/models/manifest.json`.
