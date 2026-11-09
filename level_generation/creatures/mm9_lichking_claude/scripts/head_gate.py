#!/usr/bin/env python3
"""Staff against the head (2026-11-01): per clip at 30 fps, staff vertices (Bone01 part of LichKingStaff and the staff skull) inside the convex
hull of the head skull (LichKingHead vertices led by Bip01 Head); frames and the deepest. Args: <glb> [...]"""
import sys, numpy as np
from scipy.spatial import ConvexHull
sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
for path in sys.argv[1:]:
    m=Model(Glb(path)); doc=m.glb.json; nn=[n['name'] for n in doc['nodes']]; jn=[nn[j] for j in m.joints]
    mats=[doc['materials'][p['material']]['name'] for p in doc['meshes'][0]['primitives']]; b1=jn.index('Bone01'); hi=mats.index('LichKingHead')
    hd=m.primitives[hi]; dom=np.array([jn[j] for j in hd['joints'][np.arange(len(hd['positions'])),np.argmax(hd['weights'],1)]])
    staff=[(i,np.where((m.primitives[i]['joints'][:,0]==b1)&(m.primitives[i]['weights'][:,0]>0.99))[0]) for i,n in enumerate(mats) if n.startswith('LichKingStaff')]
    out=[]
    for clip in [a['name'] for a in doc['animations']]:
        T=m.clip_times(clip)[-1]; depth=0; fr=0; nf=0
        for t in np.arange(0,T+1e-6,1/30):
            SP=m.skinned_positions(m.world(m.sample(clip,float(t)))); H=ConvexHull(SP[hi][0][dom=='Bip01 Head'])
            S=np.vstack([SP[i][0][v] for i,v in staff]); sd=(S@H.equations[:,:3].T+H.equations[:,3]).max(1); nf+=1
            if (sd<0).any(): fr+=1; depth=max(depth,float(-sd.min()))
        if fr: out.append(f'{clip} {fr}/{nf} frames, {depth*100:.1f} cm')
    print(path.split('/')[-1], 'staff inside the head (skull hull):', '; '.join(out) or 'none')
