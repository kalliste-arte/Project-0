"""
Local text-to-speech via Piper (free, offline, natural-sounding voices).
Piper binary + voice model are downloaded once during setup - see
setup/VOICE_SETUP.md.
"""
from __future__ import annotations
import subprocess
import tempfile
import os
import sounddevice as sd
import soundfile as sf


class TextToSpeech:
    def __init__(self, piper_exe: str, voice_model_path: str, speaking_rate: float = 1.0):
        self.piper_exe = piper_exe
        self.voice_model_path = voice_model_path
        self.speaking_rate = speaking_rate

    def _emotion_prefix(self, tone: str | None) -> str:
        """Light prosody shaping - Piper doesn't support SSML emotion tags,
        so tone comes from phrasing/pacing choices made upstream in brain.py.
        Kept here as a hook point if you swap in a TTS engine that does
        support emotion tags (e.g. some ElevenLabs voices)."""
        return ""

    def speak(self, text: str, tone: str | None = None):
        text = self._emotion_prefix(tone) + text
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        cmd = [
            self.piper_exe,
            "--model", self.voice_model_path,
            "--output_file", wav_path,
            "--length_scale", str(1.0 / self.speaking_rate),
        ]
        subprocess.run(cmd, input=text.encode("utf-8"), check=True)

        data, samplerate = sf.read(wav_path)
        sd.play(data, samplerate)
        sd.wait()
        os.remove(wav_path)
