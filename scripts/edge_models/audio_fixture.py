import math
import wave
from pathlib import Path


def generate_dummy_wave(
  output_path: Path,
  *,
  duration_seconds: float = 1.0,
  sample_rate: int = 16000,
) -> Path:
  output_path.parent.mkdir(parents=True, exist_ok=True)
  total_frames = int(duration_seconds * sample_rate)
  amplitude = 8000
  frequency_hz = 440.0

  with wave.open(str(output_path), 'wb') as wave_file:
    wave_file.setnchannels(1)
    wave_file.setsampwidth(2)
    wave_file.setframerate(sample_rate)

    frames = bytearray()
    for frame_index in range(total_frames):
      sample = int(
        amplitude * math.sin((2.0 * math.pi * frequency_hz * frame_index) / sample_rate)
      )
      frames.extend(sample.to_bytes(2, byteorder='little', signed=True))

    wave_file.writeframes(bytes(frames))

  return output_path