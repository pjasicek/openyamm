import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *
P,T,_=load('meshy/head_v1/model_urls_glb.glb'); print(len(P),len(T)); P,T,_,_=weld(P,T); print(len(P),len(T))
nc,l=comps(len(P),T); sz=np.bincount(l)
print('bbox',P.min(0).round(3),P.max(0).round(3))
for c in np.argsort(-sz):
    Q=P[l==c]; print(c,sz[c],np.round(Q.mean(0),3).tolist(),np.round(np.ptp(Q,0),3).tolist())
def bd(T):
    e=np.sort(np.vstack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),1); u,c=np.unique(e,axis=0,return_counts=True); return u[c==1],u[c>2]
b,nm=bd(T); print('boundary',len(b),'over',len(nm))
Tm=T[(l==np.argmax(sz))[T[:,0]]]; b,nm=bd(Tm); print('main boundary',len(b),len(nm), P[b.ravel()].mean(0).round(3) if len(b) else None)
e=np.vstack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); L=np.linalg.norm(P[e[:,0]]-P[e[:,1]],axis=1); print('edges>0.1',(L>.1).sum(),'>.06',(L>.06).sum(),'med',np.median(L))
