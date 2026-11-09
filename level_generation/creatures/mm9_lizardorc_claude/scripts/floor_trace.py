import sys; sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
m=Model(Glb('export/mm9_lizardorc.glb')); names=[n.get('name') for n in m.glb.json['nodes']]; jn=[names[j] for j in m.joints]
P=[p for p in m.primitives if p['skinned'] and p['node']==m.primitives[0]['node']]
dom=np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])),p['weights'].argmax(1)]]) for p in P]).astype(str)
for c in ('AttackMelee',):
    best=(9,0,'')
    for t in m.clip_times(c):
        x=np.vstack([q[0] for q in m.skinned_positions(m.world(m.sample(c,float(t))))[:len(P)]]); i=x[:,1].argmin()
        if x[i,1]<best[0]: best=(float(x[i,1]),float(t),dom[i])
    print(c,'lowest',round(best[0],3),'t',round(best[1],3),'on',best[2])
