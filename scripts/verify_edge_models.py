import logging
import wave
from pathlib import Path

from scripts.edge_models.manifest import DOCS_DIR, MOBILE_MODELS_DIR, EdgeModelManifest


def verify_edge_workspace() -> list[Path]:
  manifest_path = MOBILE_MODELS_DIR / 'manifest.json'
  manifest = EdgeModelManifest.model_validate_json(manifest_path.read_text(encoding='utf-8'))

  required_paths = [
    manifest_path,
    MOBILE_MODELS_DIR / 'README.md',
    MOBILE_MODELS_DIR / 'stt' / 'README.md',
    MOBILE_MODELS_DIR / 'tts' / 'README.md',
    MOBILE_MODELS_DIR / 'vision' / 'README.md',
    MOBILE_MODELS_DIR / 'fixtures' / 'dummy_transcript.txt',
    MOBILE_MODELS_DIR / 'fixtures' / 'dummy_prompt.txt',
    MOBILE_MODELS_DIR / 'fixtures' / 'dummy_audio.wav',
    DOCS_DIR / 'EDGE_MODEL_MATRIX.md',
    DOCS_DIR / 'NOTEBOOK_LLM_GUIDE.md',
    DOCS_DIR / 'PROFILING.md',
  ]

  for path in required_paths:
    if not path.exists():
      raise FileNotFoundError(f'Missing required edge-model asset: {path}')

  with wave.open(str(MOBILE_MODELS_DIR / 'fixtures' / 'dummy_audio.wav'), 'rb') as wave_file:
    if wave_file.getnchannels() != 1:
      raise ValueError('Dummy audio must be mono.')
    if wave_file.getframerate() != 16000:
      raise ValueError('Dummy audio must use a 16kHz sample rate.')
    if wave_file.getnframes() <= 0:
      raise ValueError('Dummy audio fixture must contain frames.')

  if manifest.selected_models['stt'] != 'stt-whisper-tiny-en-onnx-int8':
    raise ValueError('Unexpected default STT model selection.')
  if manifest.selected_models['tts'] != 'tts-piper-lessac-medium':
    raise ValueError('Unexpected default TTS model selection.')

  return required_paths


def main() -> int:
  logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
  verified_paths = verify_edge_workspace()
  logger = logging.getLogger('graphite.edge_models')
  logger.info('Verified %s edge-model assets.', len(verified_paths))
  return 0


if __name__ == '__main__':
  raise SystemExit(main())