import sys
sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
m=Model(Glb('export/mm9_clansoldier.glb')); n=[x.get('name') for x in m.glb.json['nodes']]
for c in ('Walking','Running','Backpedal','BackpedalRun'):
    T=m.clip_times(c); dur=T[-1]; ts=np.linspace(0,dur,61)
    zs={}
    for s in 'LR':
        p=np.array([m.world(m.sample(c,float(t)))[n.index(f'Bip01 {s} Toe0')][:3,3] for t in ts]); zs[s]=p
    out=[]
    for s,p in zs.items():
        v=np.gradient(p[:,2],ts); low=p[:,1]<np.percentile(p[:,1],35)
        out.append((float(np.median(np.abs(v[low]))), float(np.ptp(p[:,2]))))
    print(c,'dur',round(dur,3),'stance speed',[round(a,2) for a,b in out],'range',[round(b,2) for a,b in out],'stride est',round(np.mean([a for a,b in out])*dur,2))
