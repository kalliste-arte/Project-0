"""Local speech-to-text using faster-whisper. Runs fully offline."""
from __future__ import annotations
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechToText:
    def __init__(self, model_size: str = "base.en", sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def record_command(self, max_seconds: float = 8.0, silence_cutoff: float = 1.2) -> np.ndarray:
        """Records until ~silence_cutoff seconds of quiet, or max_seconds hit."""
        frames = []
        silent_chunks = 0
        chunk_dur = 0.25
        chunk_samples = int(self.sample_rate * chunk_dur)
        max_chunks = int(max_seconds / chunk_dur)
        silence_needed = int(silence_cutoff / chunk_dur)

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
            for _ in range(max_chunks):
                data, _ = stream.read(chunk_samples)
                frames.append(data.copy())
                volume = np.abs(data).mean()
                if volume < 0.01:
                    silent_chunks += 1
                    if silent_chunks >= silence_needed and len(frames) > 4:
                        break
                else:
                    silent_chunks = 0

        return np.concatenate(frames)[:, 0]

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, language="en")
        return " ".join(s.text for s in segments).strip()
