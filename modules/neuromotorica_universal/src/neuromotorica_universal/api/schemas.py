from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List
from dataclasses import dataclass
from ..core.nmj import NMJ
class SessionStartReq(BaseModel):
    exercise_id:str=Field(...,min_length=1); dt:float=Field(0.01,gt=0,le=0.1)
class SessionStartResp(BaseModel): session_id:str
class SignalReq(BaseModel): u:float=Field(...,ge=0.0,le=1.0)
class BestCueResp(BaseModel): cues:List[str]
class PolicyOutcomeReq(BaseModel): cue_text:str; success:float=Field(...,ge=0.0,le=1.0)
class SummaryReq(BaseModel): pass
class SummaryResp(BaseModel): metrics:dict
@dataclass
class Session:
    id:str; exercise_id:str; dt:float; nmj:NMJ; outputs:list=None
    def __post_init__(self):
        if self.outputs is None: self.outputs=[]
