\
from neuromotorica_universal.policy.coach import UCB1

def test_ucb1_select_and_update():
    u = UCB1(cues=["A","B","C"])
    first = u.select(k=2)
    assert len(first) == 2
    # Update rewards
    for c in first:
        u.update(c, 1.0)
    # Next selection should be valid
    nxt = u.select(k=2)
    assert len(nxt) == 2
    for c in nxt:
        assert c in ["A","B","C"]
