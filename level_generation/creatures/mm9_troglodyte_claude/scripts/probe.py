import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *; from meshlib import *
P,T,_=load('meshy/smart_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T); nc,l=comps(len(P),T)
keep=l==0; T=T[keep[T[:,0]]]
S=1.24; P=P*S; P[:,1]+= -0.594 - P[:,1].min()
print('bbox',P[keep].min(0).round(3),P[keep].max(0).round(3))
Y=np.array([0,1.,0])
for y in np.arange(0.62,-0.6,-0.06):
    L=section(P,T,np.array([0,y,0]),Y)
    print(round(y,2),[ (np.round(q['c'],3).tolist(),round(q['per'],3)) for q in sorted(L,key=lambda q:q['c'][0])])
