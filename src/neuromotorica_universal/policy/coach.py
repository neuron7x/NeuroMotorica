from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class CueStat:
    pulls: int = 0
    reward_sum: float = 0.0

    @property
    def mean(self) -> float:
        return self.reward_sum / self.pulls if self.pulls else 0.0


@dataclass
class UCB1:
    cues: list[str]
    stats: dict[str, CueStat] = field(default_factory=dict)
    t: int = 0

    def __post_init__(self) -> None:
        for cue in self.cues:
            self.stats.setdefault(cue, CueStat())

    def select(self, k: int = 1) -> list[str]:
        self.t += 1
        total = max(1, sum(stat.pulls for stat in self.stats.values()))

        def ucb(cue: str) -> float:
            stat = self.stats[cue]
            if stat.pulls == 0:
                return float("inf")
            return stat.mean + math.sqrt(2.0 * math.log(total) / stat.pulls)

        ranked = sorted(self.cues, key=ucb, reverse=True)
        return ranked[: max(1, k)]

    def update(self, cue: str, reward: float) -> None:
        if cue not in self.stats:
            raise KeyError(cue)
        stat = self.stats[cue]
        stat.pulls += 1
        stat.reward_sum += float(reward)
