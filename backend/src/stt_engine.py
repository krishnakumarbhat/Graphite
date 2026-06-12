"""Speech-to-text engine.

Priority:
1. HuggingFace Inference API (whisper-large-v3) — no local model, low latency
2. Local pywhispercpp — fallback when HF_TOKEN is not set

This avoids the 30-second timeout that came from loading/running the model locally.
"""

import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from src.errors import ConfigurationError

logger = logging.getLogger('graphite.stt')

# HF Inference API endpoint for Whisper
_HF_WHISPER_URL = 'https://api-inference.huggingface.co/models/openai/whisper-large-v3'


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


def _transcribe_via_hf_api(audio_path: Path, token: str) -> str:
    """Send audio bytes to HuggingFace Inference API and return transcript."""
    import httpx

    audio_bytes = audio_path.read_bytes()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'audio/wav',
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(_HF_WHISPER_URL, content=audio_bytes, headers=headers)
        response.raise_for_status()
        payload = response.json()
        # Response is {"text": "..."}
        text = str(payload.get('text', '')).strip()
        if not text:
            raise ConfigurationError('HuggingFace Whisper returned an empty transcript.')
        return text
    except httpx.HTTPStatusError as err:
        raise ConfigurationError(
            f'HuggingFace Whisper API error ({err.response.status_code}): {err.response.text}'
        ) from err
    except httpx.RequestError as err:
        raise ConfigurationError(f'HuggingFace Whisper connection error: {err}') from err


def _transcribe_via_local_whisper(
    audio_path: Path,
    *,
    model_path: 'Path | str | None',
    artifact_repo_id: str = '',
    cache_dir: 'Path | str | None' = None,
    token: 'str | None' = None,
) -> str:
    """Fallback: run pywhispercpp locally."""
    from functools import lru_cache

    resolved_model = _resolve_voice_input_model_path(
        model_path,
        artifact_repo_id=artifact_repo_id,
        cache_dir=cache_dir,
        token=token,
    )
    if resolved_model is None:
        raise ConfigurationError(
            'Voice input model is unavailable. '
            'Set HF_TOKEN for remote Whisper or set VOICE_INPUT_MODEL_PATH for local model.'
        )

    @lru_cache(maxsize=2)
    def _load_model(path: str):
        from pywhispercpp.model import Model
        return Model(
            path,
            language='en',
            print_progress=False,
            print_realtime=False,
            print_special=False,
            print_timestamps=False,
        )

    model = _load_model(str(resolved_model))
    segments = model.transcribe(str(audio_path))
    transcript = ' '.join(
        segment.text.strip()
        for segment in segments
        if getattr(segment, 'text', '').strip()
    ).strip()
    if not transcript:
        raise ConfigurationError('No speech was detected in the uploaded audio clip.')
    return transcript


def _resolve_voice_input_model_path(
    configured_path: 'Path | str | None',
    *,
    artifact_repo_id: str = '',
    cache_dir: 'Path | str | None' = None,
    token: 'str | None' = None,
) -> 'Path | None':
    candidates: list[Path] = []
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    candidates.extend([
        Path.home() / 'Desktop' / 'voice-input-english-244.bin',
        (
            Path(__file__).resolve().parent.parent
            / 'data'
            / 'models'
            / 'stt'
            / 'voice-input-english-244.bin'
        ),
    ])
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    if not artifact_repo_id:
        return None

    try:
        from huggingface_hub import hf_hub_download
        resolved_cache = (
            Path(cache_dir).expanduser() if cache_dir else Path.home() / '.cache' / 'graphite'
        )
        resolved_cache.mkdir(parents=True, exist_ok=True)
        return Path(hf_hub_download(
            repo_id=artifact_repo_id,
            filename='voice-input-english-244.bin',
            cache_dir=str(resolved_cache),
            token=token or None,
        ))
    except Exception:
        return None


def transcribe_audio_file(
    source_path: Path,
    *,
    model_path: 'Path | str | None',
    artifact_repo_id: str = '',
    cache_dir: 'Path | str | None' = None,
    token: 'str | None' = None,
) -> str:
    """Transcribe audio.

    Uses HuggingFace Inference API (Whisper large-v3) when ``token`` is set,
    otherwise falls back to local pywhispercpp.
    """
    with TemporaryDirectory(prefix='graphite-stt-') as temp_dir:
        normalized_path = Path(temp_dir) / 'normalized.wav'
        _normalize_audio_to_wav(source_path, normalized_path)

        if token and token.strip():
            logger.info('Transcribing via HuggingFace Whisper API (remote)')
            try:
                return _transcribe_via_hf_api(normalized_path, token.strip())
            except ConfigurationError as hf_err:
                logger.warning(
                    'HF Whisper API failed, attempting local fallback: %s', hf_err
                )
                # Fall through to local

        logger.info('Transcribing via local pywhispercpp model')
        return _transcribe_via_local_whisper(
            normalized_path,
            model_path=model_path,
            artifact_repo_id=artifact_repo_id,
            cache_dir=cache_dir,
            token=token,
        )