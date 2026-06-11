import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download


ESPEAK_VOICE_MAP = {
  'Bella': 'en-us+f3',
  'Luna': 'en-us+f3',
  'Rosie': 'en-us+f4',
  'Kiki': 'en-us+f4',
  'Bruno': 'en-us+m3',
  'Jasper': 'en-us+m3',
  'Hugo': 'en-us+m4',
  'Leo': 'en-us+m4',
}


def ensure_tts_output_dir(output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  return output_dir


def inspect_audio_file(file_path: Path) -> dict[str, Any]:
  metadata = {
    'size_bytes': file_path.stat().st_size,
    'duration_seconds': None,
    'sample_rate_hz': None,
  }

  try:
    result = subprocess.run(
      [
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'stream=sample_rate:format=duration,size',
        '-of',
        'json',
        str(file_path),
      ],
      capture_output=True,
      check=True,
      text=True,
    )
    payload = json.loads(result.stdout or '{}')
    streams = payload.get('streams', [])
    if streams:
      sample_rate = streams[0].get('sample_rate')
      metadata['sample_rate_hz'] = int(float(sample_rate)) if sample_rate else None
    duration_value = payload.get('format', {}).get('duration')
    if duration_value is not None:
      metadata['duration_seconds'] = round(float(duration_value), 3)
  except Exception:
    return metadata

  return metadata


def synthesize_with_espeak(*, text: str, output_path: Path, voice: str, speed: float) -> None:
  espeak_voice = ESPEAK_VOICE_MAP.get(voice, voice if voice.startswith('en') else 'en-us+m3')
  rate = str(int(max(min(175 * speed, 320), 110)))
  subprocess.run(
    ['espeak', '--stdin', '-v', espeak_voice, '-s', rate, '-w', str(output_path)],
    input=text,
    capture_output=True,
    check=True,
    text=True,
  )
def _download_kitten_model_from_repo(
  *,
  repo_id: str,
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
        filename='kitten_tts_mini_v0_8.onnx',
        cache_dir=str(resolved_cache_dir),
        token=token or None,
      )
    )
  except Exception:
    return None


def _resolve_kitten_model_path(
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
      Path.home() / 'Desktop' / 'kitten_tts_mini_v0_8.onnx',
      (
        Path(__file__).resolve().parent.parent
        / 'data'
        / 'models'
        / 'tts'
        / 'kitten_tts_mini_v0_8.onnx'
      ),
    ]
  )

  for candidate in candidates:
    if candidate.exists() and candidate.is_file():
      return candidate

  return _download_kitten_model_from_repo(
    repo_id=artifact_repo_id,
    cache_dir=cache_dir,
    token=token,
  )


def _download_kitten_support_file(
  *,
  repo_ids: list[str],
  filename: str,
  cache_dir: Path,
  token: str | None,
) -> Path:
  last_error: Exception | None = None
  for repo_id in repo_ids:
    if not repo_id:
      continue
    try:
      return Path(
        hf_hub_download(
          repo_id=repo_id,
          filename=filename,
          cache_dir=str(cache_dir),
          token=token or None,
        )
      )
    except Exception as error:
      last_error = error

  raise RuntimeError(f'Unable to download {filename} from any configured Hugging Face repo.') from last_error


def _load_local_kitten_model(
  *,
  model_path: Path,
  repo_ids: list[str],
  cache_dir: Path,
  token: str | None,
):
  from kittentts.onnx_model import KittenTTS_1_Onnx

  cache_dir.mkdir(parents=True, exist_ok=True)
  config_path = _download_kitten_support_file(
    repo_ids=repo_ids,
    filename='config.json',
    cache_dir=cache_dir,
    token=token,
  )
  with config_path.open(encoding='utf-8') as handle:
    config = json.load(handle)

  voices_path = _download_kitten_support_file(
    repo_ids=repo_ids,
    filename=config['voices'],
    cache_dir=cache_dir,
    token=token,
  )

  return KittenTTS_1_Onnx(
    model_path=str(model_path),
    voices_path=str(voices_path),
    speed_priors=config.get('speed_priors', {}),
    voice_aliases=config.get('voice_aliases', {}),
  )


@lru_cache(maxsize=2)
def load_kitten_model(
  model_name: str,
  local_model_path: str | None = None,
  cache_dir: str | None = None,
  artifact_repo_id: str = '',
  token: str | None = None,
):
  from kittentts import KittenTTS

  resolved_model_path = _resolve_kitten_model_path(local_model_path)
  resolved_cache_dir = (
    Path(cache_dir).expanduser()
    if cache_dir
    else Path.home() / '.cache' / 'graphite'
  )
  repo_ids = [repo_id for repo_id in [artifact_repo_id, model_name] if repo_id]

  if resolved_model_path is not None:
    return _load_local_kitten_model(
      model_path=resolved_model_path,
      repo_ids=repo_ids,
      cache_dir=resolved_cache_dir,
      token=token,
    )

  return KittenTTS(model_name, cache_dir=str(resolved_cache_dir))


def synthesize_with_kitten(
  *,
  text: str,
  output_path: Path,
  voice: str,
  speed: float,
  model_name: str,
  local_model_path: Path | str | None,
  cache_dir: Path | str | None,
  artifact_repo_id: str = '',
  token: str | None = None,
) -> None:
  import soundfile as sf

  resolved_model_path = _resolve_kitten_model_path(
    local_model_path,
    artifact_repo_id=artifact_repo_id,
    cache_dir=cache_dir,
    token=token,
  )

  model = load_kitten_model(
    model_name,
    str(resolved_model_path) if resolved_model_path else None,
    str(cache_dir) if cache_dir else None,
    artifact_repo_id=artifact_repo_id,
    token=token,
  )
  audio = model.generate(
    text,
    voice=voice,
    speed=speed,
    clean_text=True,
  )
  sf.write(str(output_path), audio, 24000)