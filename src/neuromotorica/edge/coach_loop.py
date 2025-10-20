from __future__ import annotations
import json, time, pathlib
from ..common.events import RepEvent, CueEvent, asdict
from .policy.engine import PolicyEngine
from .policy.safety import SafetyGate
from .tts.tts import VoiceCoach

DEFAULT_CADENCE = (1.2, 0.4, 0.8)

def run_demo(data_path: str) -> None:
    pp = pathlib.Path(data_path)
    data = json.loads(pp.read_text(encoding="utf-8"))
    policy = PolicyEngine()
    safety = SafetyGate()
    tts = VoiceCoach()

    for item in data:
        rep = RepEvent(**item)
        flags = safety.check(rep.knee_valgus_deg, rep.concentric_velocity)
        faults = rep.faults + flags
        cue_text, reason = policy.select(faults, rep.arousal)
        cue = CueEvent(t=rep.t, text=cue_text, reason=reason, cadence=DEFAULT_CADENCE)
        print(json.dumps({"rep": asdict(rep), "cue": asdict(cue)}, ensure_ascii=False))
        tts.speak_with_cadence(cue.text, cue.cadence)
        time.sleep(0.01)
