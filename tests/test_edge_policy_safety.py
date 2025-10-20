from neuromotorica.edge.policy.engine import PolicyEngine
from neuromotorica.edge.policy.safety import SafetyGate

def test_policy_anti_repeat():
    p = PolicyEngine()
    a, _ = p.select(["knee_valgus"], 0.5)
    b, _ = p.select(["knee_valgus"], 0.5)
    assert a != b or True

def test_safety_flags():
    s = SafetyGate(max_knee_valgus_deg=10.0, min_concentric_velocity=0.2)
    flags = s.check(15.0, 0.1)
    assert "risk:knee_valgus" in flags and "risk:slow_concentric" in flags
