from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
MOBILE_MODELS_DIR = REPO_ROOT / 'mobile' / 'models'
DOCS_DIR = REPO_ROOT / 'docs'


class ScoreCard(BaseModel):
  accuracy: int = Field(ge=1, le=10)
  latency: int = Field(ge=1, le=10)
  footprint: int = Field(ge=1, le=10)
  onnx_readiness: int = Field(ge=1, le=10)
  mobile_packaging: int = Field(ge=1, le=10)

  def weighted_total(self) -> float:
    return round(
      (self.accuracy * 0.35)
      + (self.latency * 0.20)
      + (self.footprint * 0.15)
      + (self.onnx_readiness * 0.15)
      + (self.mobile_packaging * 0.15),
      2,
    )


class EdgeModelCandidate(BaseModel):
  model_id: str
  task: Literal['stt', 'tts']
  family: str
  variant: str
  source: str
  quantization: str
  approximate_size_mb: int = Field(ge=1)
  artifacts: list[str]
  recommended: bool = False
  notes: str
  scorecard: ScoreCard


class EdgeModelManifest(BaseModel):
  version: str = '1.0'
  selection_mode: str
  constraints: dict[str, str]
  selected_models: dict[str, str]
  candidates: list[EdgeModelCandidate]
  fixtures: list[str]
  validation_metrics: list[str]


def build_default_manifest() -> EdgeModelManifest:
  candidates = [
    EdgeModelCandidate(
      model_id='stt-whisper-tiny-en-onnx-int8',
      task='stt',
      family='Whisper',
      variant='tiny.en',
      source='openai/whisper-tiny.en exported to ONNX',
      quantization='int8',
      approximate_size_mb=78,
      artifacts=[
        'mobile/models/stt/whisper-tiny-en-int8/encoder_model.onnx',
        'mobile/models/stt/whisper-tiny-en-int8/decoder_model.onnx',
        'mobile/models/stt/whisper-tiny-en-int8/config.json',
      ],
      recommended=True,
      notes=(
        'Best current balance for on-device English transcription, '
        'ONNX portability, and APK footprint.'
      ),
      scorecard=ScoreCard(
        accuracy=7,
        latency=9,
        footprint=9,
        onnx_readiness=10,
        mobile_packaging=9,
      ),
    ),
    EdgeModelCandidate(
      model_id='stt-whisper-base-en-onnx-int8',
      task='stt',
      family='Whisper',
      variant='base.en',
      source='openai/whisper-base.en exported to ONNX',
      quantization='int8',
      approximate_size_mb=142,
      artifacts=[
        'mobile/models/stt/whisper-base-en-int8/encoder_model.onnx',
        'mobile/models/stt/whisper-base-en-int8/decoder_model.onnx',
        'mobile/models/stt/whisper-base-en-int8/config.json',
      ],
      notes=(
        'Higher ceiling than Tiny, but a weaker fit for mobile cold-start '
        'and storage constraints.'
      ),
      scorecard=ScoreCard(
        accuracy=8,
        latency=7,
        footprint=7,
        onnx_readiness=10,
        mobile_packaging=7,
      ),
    ),
    EdgeModelCandidate(
      model_id='stt-sensevoice-small-onnx-int8',
      task='stt',
      family='SenseVoice',
      variant='small',
      source='FunAudioLLM/SenseVoiceSmall exported to ONNX',
      quantization='int8',
      approximate_size_mb=185,
      artifacts=[
        'mobile/models/stt/sensevoice-small-int8/model.onnx',
        'mobile/models/stt/sensevoice-small-int8/config.json',
      ],
      notes=(
        'Strong multilingual accuracy, but the export and mobile packaging '
        'path is riskier than Whisper Tiny today.'
      ),
      scorecard=ScoreCard(
        accuracy=9,
        latency=8,
        footprint=6,
        onnx_readiness=7,
        mobile_packaging=6,
      ),
    ),
    EdgeModelCandidate(
      model_id='tts-piper-lessac-medium',
      task='tts',
      family='Piper',
      variant='en_US-lessac-medium',
      source='rhasspy/piper voice package',
      quantization='onnx-native',
      approximate_size_mb=63,
      artifacts=[
        'mobile/models/tts/piper-lessac-medium/en_US-lessac-medium.onnx',
        'mobile/models/tts/piper-lessac-medium/en_US-lessac-medium.onnx.json',
      ],
      recommended=True,
      notes=(
        'Best current open-source fit for CPU-only mobile TTS with low '
        'integration risk and native ONNX delivery.'
      ),
      scorecard=ScoreCard(
        accuracy=8,
        latency=9,
        footprint=8,
        onnx_readiness=10,
        mobile_packaging=10,
      ),
    ),
    EdgeModelCandidate(
      model_id='tts-coqui-vits-ljspeech',
      task='tts',
      family='Coqui VITS',
      variant='ljspeech',
      source='coqui-ai/TTS exported to ONNX',
      quantization='fp16/int8 mixed',
      approximate_size_mb=118,
      artifacts=[
        'mobile/models/tts/coqui-vits-ljspeech/model.onnx',
        'mobile/models/tts/coqui-vits-ljspeech/config.json',
      ],
      notes='Higher integration and runtime risk on mobile than Piper for a modest quality gain.',
      scorecard=ScoreCard(
        accuracy=8,
        latency=7,
        footprint=6,
        onnx_readiness=7,
        mobile_packaging=6,
      ),
    ),
    EdgeModelCandidate(
      model_id='tts-kokoro-82m-onnx',
      task='tts',
      family='Kokoro',
      variant='82M',
      source='Kokoro family exported to ONNX',
      quantization='fp16/int8 mixed',
      approximate_size_mb=160,
      artifacts=[
        'mobile/models/tts/kokoro-82m/model.onnx',
        'mobile/models/tts/kokoro-82m/config.json',
      ],
      notes=(
        'Natural sounding, but currently too heavy for the repo constraint '
        'of small local storage and low-friction APK delivery.'
      ),
      scorecard=ScoreCard(
        accuracy=9,
        latency=6,
        footprint=5,
        onnx_readiness=6,
        mobile_packaging=5,
      ),
    ),
  ]

  return EdgeModelManifest(
    selection_mode=(
      'mobile-first for a 4 GB RTX 3050 training or export budget '
      'and APK packaging constraints'
    ),
    constraints={
      'target_runtime': 'Android APK with on-device inference',
      'hardware_budget': '4 GB RTX 3050 and CPU fallback',
      'storage_budget': 'keep model payloads compact',
      'integration_policy': 'prefer ONNX-native or ONNX-exportable models with low mobile risk',
    },
    selected_models={
      'stt': 'stt-whisper-tiny-en-onnx-int8',
      'tts': 'tts-piper-lessac-medium',
    },
    candidates=candidates,
    fixtures=[
      'mobile/models/fixtures/dummy_audio.wav',
      'mobile/models/fixtures/dummy_transcript.txt',
      'mobile/models/fixtures/dummy_prompt.txt',
    ],
    validation_metrics=[
      'WER',
      'CER',
      'real_time_factor',
      'peak_memory_mb',
      'apk_asset_size_mb',
    ],
  )