import pytest

from neuromotorica_universal.policy.coach import UCB1


def test_ucb1_select_and_update() -> None:
    policy = UCB1(cues=["A", "B", "C"])

    first = policy.select(k=2)
    assert len(first) == 2

    for cue in first:
        policy.update(cue, 1.0)

    nxt = policy.select(k=2)
    assert len(nxt) == 2
    for cue in nxt:
        assert cue in {"A", "B", "C"}


def test_ucb1_update_unknown_cue_raises() -> None:
    policy = UCB1(cues=["A"])

    with pytest.raises(KeyError):
        policy.update("unknown", 1.0)
