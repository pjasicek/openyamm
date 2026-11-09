import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *; from meshlib import *
P,T,_=load('meshy/smart_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T); nc,l=comps(len(P),T); T=T[(l==0)[T[:,0]]]
S=1.24; P=P*S; P[:,1]+= -0.594 - P[:,1].min()
X=np.array([1.,0,0])
for x in np.arange(.10,.31,.02):
    L=section(P,T,np.array([x,0,0]),X)
    print(round(x,2),[ (np.round(q['c'][1:],3).tolist(),round(q['per'],3)) for q in sorted(L,key=lambda q:-q['per']) if q['c'][1]>0.0])
# leg/foot
for x in (.1,.15,.2,.25,.3):
    L=section(P,T,np.array([x,0,0]),X)
    print(round(x,2),[ (np.round(q['c'][1:],3).tolist(),round(q['per'],3)) for q in sorted(L,key=lambda q:-q['per']) if q['c'][1]<=0.0])
# foot bottom
m=P[:,1]<-0.5; print('foot',P[m&(P[:,0]>0)].min(0).round(3),P[m&(P[:,0]>0)].max(0).round(3))
