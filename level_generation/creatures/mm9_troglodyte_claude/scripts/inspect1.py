import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *
P,T,_=load(sys.argv[1]); P,T,_,_=weld(P,T); print(len(P),len(T))
nc,l=comps(len(P),T); print(nc)
sz=np.bincount(l)
for c in np.argsort(-sz)[:90]:
    Q=P[l==c]; print(c,sz[c],np.round(Q.mean(0),3).tolist(),np.round(np.ptp(Q,0),3).tolist())
# long edges
e=np.vstack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); L=np.linalg.norm(P[e[:,0]]-P[e[:,1]],axis=1)
o=np.argsort(-L)[:30]; print(np.round(L[o],3)); print(P[e[o[0]]])
a=np.linalg.norm(np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]),axis=1)/2
E0=np.linalg.norm(P[T[:,1]]-P[T[:,0]],axis=1);E1=np.linalg.norm(P[T[:,2]]-P[T[:,1]],axis=1);E2=np.linalg.norm(P[T[:,0]]-P[T[:,2]],axis=1)
print('sliver faces', ((np.maximum.reduce([E0,E1,E2])>0.04)&(a/np.maximum.reduce([E0,E1,E2])**2<0.02)).sum())
print('median edge',np.median(L))
