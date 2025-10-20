from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple

@dataclass
class RepEvent:
    t: float
    rep_idx: int
    knee_valgus_deg: float
    concentric_velocity: float
    arousal: float  # 0..1
    faults: List[str] = field(default_factory=list)

@dataclass
class CueEvent:
    t: float
    text: str
    reason: str
    cadence: Tuple[float, float, float]

@dataclass
class SetSummary:
    set_idx: int
    reps: int
    flags: List[str] = field(default_factory=list)

@dataclass
class PolicyUpdate:
    user_id: str
    exercise_id: str
    cue_text: str
    success: bool

def asdict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError("Unsupported type for asdict")
