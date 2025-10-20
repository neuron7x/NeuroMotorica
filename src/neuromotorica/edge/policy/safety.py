from __future__ import annotations

class SafetyGate:
    def __init__(self, max_knee_valgus_deg: float = 12.0, min_concentric_velocity: float = 0.15):
        self.max_knee_valgus_deg = max_knee_valgus_deg
        self.min_concentric_velocity = min_concentric_velocity

    def check(self, knee_valgus_deg: float, concentric_velocity: float) -> list[str]:
        flags: list[str] = []
        if knee_valgus_deg > self.max_knee_valgus_deg:
            flags.append("risk:knee_valgus")
        if concentric_velocity < self.min_concentric_velocity:
            flags.append("risk:slow_concentric")
        return flags
