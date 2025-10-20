from __future__ import annotations
import json, pathlib, random
from typing import List

class PolicyEngine:
    def __init__(self, cues_path: str | None = None):
        if cues_path is None:
            cues_path = str(pathlib.Path(__file__).with_name("cues.json"))
        with open(cues_path, "r", encoding="utf-8") as f:
            self.cues = json.load(f)
        self._last: dict[str, str] = {}

    def select(self, faults: List[str], arousal: float) -> tuple[str, str]:
        key = faults[0] if faults else "neutral"
        options = self.cues.get(key, self.cues["neutral"])
        choices = [c for c in options if self._last.get(key) != c] or options
        cue = random.choice(choices)
        self._last[key] = cue
        reason = f"fault:{key}; arousal:{arousal:.2f}"
        return cue, reason
