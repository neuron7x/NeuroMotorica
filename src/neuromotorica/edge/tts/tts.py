from __future__ import annotations
from typing import Tuple
import os
try:
    import pyttsx3
except Exception:  # pragma: no cover
    pyttsx3 = None

class VoiceCoach:
    def __init__(self, enable_audio: bool | None = None):
        if enable_audio is None:
            enable_audio = os.getenv("NEUROMOTORICA_AUDIO", "0") == "1"
        self.enable_audio = enable_audio and (pyttsx3 is not None)
        self.engine = pyttsx3.init() if self.enable_audio else None

    def speak_with_cadence(self, text: str, cadence: Tuple[float, float, float]) -> None:
        ecc, iso, con = cadence
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        print(f"[TTS cadence ecc:{ecc:.2f}s iso:{iso:.2f}s con:{con:.2f}s] {text}")
