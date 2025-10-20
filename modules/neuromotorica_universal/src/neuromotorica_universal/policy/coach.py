from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List
@dataclass
class CueStat: pulls:int=0; reward_sum:float=0.0
@property
def mean(self)->float: return self.reward_sum/self.pulls if self.pulls else 0.0
@dataclass
class UCB1:
    cues: List[str]; stats: Dict[str, CueStat]=field(default_factory=dict); t:int=0
    def __post_init__(self): 
        for c in self.cues: self.stats.setdefault(c, CueStat())
    def select(self,k:int=1)->List[str]:
        self.t+=1; total=max(1,sum(s.pulls for s in self.stats.values()))
        def ucb(c:str)->float:
            s=self.stats[c]; 
            return float('inf') if s.pulls==0 else s.mean+math.sqrt(2.0*math.log(total)/s.pulls)
        return sorted(self.cues,key=lambda c: ucb(c), reverse=True)[:max(1,k)]
    def update(self,cue:str,reward:float)->None:
        if cue not in self.stats: raise KeyError(cue)
        s=self.stats[cue]; s.pulls+=1; s.reward_sum+=float(reward)
