"""
Wake word detection.

Default approach: rolling short audio buffer transcribed by a tiny
local Whisper model, checked for the wake word. Zero external accounts
needed, works out of the box, costs a bit more CPU than a dedicated
wake-word engine.

Swap-in option (lower CPU, higher accuracy): Picovoice Porcupine with
a free custom "Aya" .ppn file generated at console.picovoice.ai.
See setup/WAKE_WORD_UPGRADE.md for that path once the basics are working.
"""
from __future__ import annotations
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class WakeWordListener:
    def __init__(self, wake_word: str = "aya", sample_rate: int = 16000,
                 window_seconds: float = 1.5):
        self.wake_word = wake_word.lower().strip()
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self._q: queue.Queue = queue.Queue()
        # "tiny" model: fast enough to run continuously, ok accuracy for a short keyword
        self._model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    def _callback(self, indata, frames, time_info, status):
        self._q.put(indata.copy())

    def listen_for_wake(self) -> bool:
        """Blocks until the wake word is heard, then returns True."""
        buf = np.zeros((0, 1), dtype=np.float32)
        window_samples = int(self.window_seconds * self.sample_rate)

        with sd.InputStream(samplerate=self.sample_rate, channels=1,
                             callback=self._callback):
            while True:
                chunk = self._q.get()
                buf = np.concatenate([buf, chunk])
                if len(buf) >= window_samples:
                    audio = buf[-window_samples:, 0]
                    buf = buf[-window_samples // 2:]  # keep overlap, drop old

                    segments, _ = self._model.transcribe(audio, language="en")
                    text = " ".join(s.text for s in segments).lower()
                    if self.wake_word in text:
                        return True
