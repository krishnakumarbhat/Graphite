import subprocess
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory

from huggingface_hub import hf_hub_download

from src.errors import ConfigurationError


def _download_model_from_repo(
  *,
  repo_id: str,
  filename: str,
  cache_dir: Path | str | None,
  token: str | None,
) -> Path | None:
  if not repo_id:
    return None

  resolved_cache_dir = (
    Path(cache_dir).expanduser()
    if cache_dir
    else Path.home() / '.cache' / 'graphite'
  )
  resolved_cache_dir.mkdir(parents=True, exist_ok=True)

  try:
    return Path(
      hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        cache_dir=str(resolved_cache_dir),
        token=token or None,
      )
    )
  except Exception:
    return None


def resolve_voice_input_model_path(
  configured_path: Path | str | None,
  *,
  artifact_repo_id: str = '',
  cache_dir: Path | str | None = None,
  token: str | None = None,
) -> Path | None:
  candidates: list[Path] = []

  if configured_path:
    candidates.append(Path(configured_path).expanduser())

  candidates.extend(
    [
      Path.home() / 'Desktop' / 'voice-input-english-244.bin',
      (
        Path(__file__).resolve().parent.parent
        / 'data'
        / 'models'
        / 'stt'
        / 'voice-input-english-244.bin'
      ),
    ]
  )

  for candidate in candidates:
    if candidate.exists() and candidate.is_file():
      return candidate

  return _download_model_from_repo(
    repo_id=artifact_repo_id,
    filename='voice-input-english-244.bin',
    cache_dir=cache_dir,
    token=token,
  )


def _normalize_audio_to_wav(source_path: Path, destination_path: Path) -> None:
  result = subprocess.run(
    [
      'ffmpeg',
      '-y',
      '-i',
      str(source_path),
      '-ar',
      '16000',
      '-ac',
      '1',
      str(destination_path),
    ],
    capture_output=True,
    text=True,
  )
  if result.returncode != 0:
    raise ConfigurationError(
      f'ffmpeg could not prepare the uploaded audio: {result.stderr.strip()}'
    )


@lru_cache(maxsize=2)
def load_voice_input_model(model_path: str):
  from pywhispercpp.model import Model

  return Model(
    model_path,
    language='en',
    print_progress=False,
    print_realtime=False,
    print_special=False,
    print_timestamps=False,
  )


def transcribe_audio_file(
  source_path: Path,
  *,
  model_path: Path | str | None,
  artifact_repo_id: str = '',
  cache_dir: Path | str | None = None,
  token: str | None = None,
) -> str:
  resolved_model_path = resolve_voice_input_model_path(
    model_path,
    artifact_repo_id=artifact_repo_id,
    cache_dir=cache_dir,
    token=token,
  )
  if resolved_model_path is None:
    raise ConfigurationError(
      'Voice input model is unavailable. '
      'Set VOICE_INPUT_MODEL_PATH or configure GRAPHITE_MODEL_REPO.'
    )

  with TemporaryDirectory(prefix='graphite-stt-') as temp_dir:
    normalized_audio_path = Path(temp_dir) / 'normalized.wav'
    _normalize_audio_to_wav(source_path, normalized_audio_path)

    model = load_voice_input_model(str(resolved_model_path))
    segments = model.transcribe(str(normalized_audio_path))

  transcript = ' '.join(
    segment.text.strip()
    for segment in segments
    if getattr(segment, 'text', '').strip()
  ).strip()
  if not transcript:
    raise ConfigurationError('No speech was detected in the uploaded audio clip.')
  return transcript