import sys; sys.path.insert(0,'scripts')
import numpy as np
from loadglb import *
P,T,_=load('meshy/head_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T)
nc,l=comps(len(P),T); sz=np.bincount(l)
print(len(P),len(T),'bbox',P.min(0).round(3),P.max(0).round(3))
for c in np.argsort(-sz)[:62]:
    q=P[l==c]; print(c,sz[c],q.min(0).round(3).tolist(),q.max(0).round(3).tolist())
main=sz.argmax(); m=l==main
print('mirror test')
from scipy.spatial import cKDTree
for X0 in (-.01,-.005,0,.005,.01):
    d,_=cKDTree(P[m]*[-1,1,1]+[2*X0,0,0]).query(P[m]); print(X0,d.mean().round(4),np.percentile(d,99).round(4))
np.savez('work/mhead0.npz',P=P,T=T,l=l)
