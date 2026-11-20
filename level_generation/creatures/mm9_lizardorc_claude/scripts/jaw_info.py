import sys; sys.path.insert(0,'scripts')
import numpy as np
sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb,Model
m=Model(Glb('source/true/lizardorc_true.glb')); doc=m.glb.json; names=[n.get('name') for n in doc['nodes']]; ix={n:i for i,n in enumerate(names)}
W0=m.world({}); H=np.linalg.inv(W0[ix['Bip01 Head']]); J=W0[ix['Box01']]
tip0=np.array([0,.63,.46,1.])
print('jaw tip rest in world',tip0[:3]); 
def rel(W): return np.linalg.inv(W[ix['Bip01 Head']])@W[ix['Box01']]
R0=rel(W0)
for a in doc['animations']:
    n=a['name']; ts=m.clip_times(n); 
    if len(ts)==0: continue
    vals=[]
    for t in np.linspace(0,ts[-1],40):
        W=m.world(m.sample(n,float(t))); Rr=np.linalg.inv(R0)@rel(W)
        # jaw tip local to Box01, in head frame compare
        p=(W0[ix['Box01']]@(R0@np.linalg.inv(R0))); 
        ang=np.degrees(np.arccos(np.clip((np.trace(Rr[:3,:3])-1)/2,-1,1)))
        axis=np.array([Rr[2,1]-Rr[1,2],Rr[0,2]-Rr[2,0],Rr[1,0]-Rr[0,1]])
        # world axis at rest frame
        ax=(W0[ix['Box01']][:3,:3]@axis); 
        vals.append((ang,np.sign(ax[0]) if np.abs(ax).sum()>1e-6 else 0))
    a_=np.array(vals); print(n,'max',a_[:,0].max().round(1),'sign',a_[a_[:,0].argmax(),1])
