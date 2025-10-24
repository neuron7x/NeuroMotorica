# SPDX-License-Identifier: Apache-2.0
import numpy as np
def _profile_params(profile:str)->dict:
    return {"warmup":2,"batch":1} if profile=="light" else {"warmup":3,"batch":4} if profile=="standard" else {"warmup":5,"batch":8}
def bench_thompson(n:int, seed:int, profile:str)->int:
    np.random.seed(seed); ops=0; p=_profile_params(profile)
    for _ in range(p["warmup"]): _=np.random.random(10000).sum()
    rewards = np.random.binomial(1, 0.3, size=n)
    a,b=1.0,1.0
    for i in range(n):
        _ = np.random.beta(a,b); a += rewards[i]; b += 1-rewards[i]; ops+=1
    return ops
def bench_linucb(n:int, seed:int, profile:str)->int:
    np.random.seed(seed); ops=0; d=8; A=np.eye(d); b=np.zeros(d)
    X=np.random.randn(n,d); r=np.random.randn(n)
    for i in range(n):
        theta=np.linalg.solve(A,b); _=X[i].dot(theta); A+=np.outer(X[i],X[i]); b+=r[i]*X[i]; ops+=1
    return ops
def bench_egreedy(n:int, seed:int, profile:str)->int:
    np.random.seed(seed); ops=0; eps=0.1; Q=np.zeros(10); N=np.zeros(10)
    for i in range(n):
        a=np.random.randint(0,10) if np.random.rand()<eps else int(np.argmax(Q))
        r=np.random.randn(); N[a]+=1; Q[a]+= (r-Q[a])/max(1,N[a]); ops+=1
    return ops
