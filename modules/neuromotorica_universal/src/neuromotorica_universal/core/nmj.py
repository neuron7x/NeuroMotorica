from __future__ import annotations
import numpy as np
from dataclasses import dataclass
@dataclass(frozen=True)
class SimulationMetrics:
    reps:int; tempo:float; range_of_motion:float; peak_force:float
class NMJ:
    def __init__(self, dt:float=0.01, tau:float=0.15, gain:float=1.8, noise:float=0.0):
        if not (0<dt<=0.1): raise ValueError
        if tau<=0 or gain<=0 or noise<0: raise ValueError
        self.dt, self.tau, self.gain, self.noise = dt,tau,gain,noise
        self.y=0.0; self._y_hist=[]; self._u_hist=[]
    def reset(self): self.y=0.0; self._y_hist.clear(); self._u_hist.clear()
    def step(self,u:float)->float:
        import numpy as np
        u=float(np.clip(u,0.0,1.0))
        dy= (-(self.y)+ self.gain*u)*(self.dt/self.tau)
        y=self.y+dy
        if self.noise>0: y+=np.random.normal(0.0,self.noise)
        self.y=float(np.clip(y,0.0,1.0))
        self._u_hist.append(u); self._y_hist.append(self.y)
        return self.y
    def simulate(self, u_seq): 
        import numpy as np
        self.reset(); out=np.empty_like(u_seq,dtype=float)
        for i,u in enumerate(u_seq): out[i]=self.step(float(u)); 
        return out
    def metrics(self)->SimulationMetrics:
        import numpy as np
        if not self._y_hist: return SimulationMetrics(0,0.0,0.0,0.0)
        y=np.asarray(self._y_hist,dtype=float); thr=0.8
        ups=(y[1:]>=thr)&(y[:-1]<thr); reps=int(np.sum(ups))
        duration=len(y)*self.dt; tempo=float(reps/duration) if duration>0 else 0.0
        rom=float(np.max(y)-np.min(y)); peak=float(np.max(y))
        return SimulationMetrics(reps,tempo,rom,peak)
