import sys
import numpy as np
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
g=Glb('level_generation/creatures/mm9_ghoul_claude/source/g1/ghoul1_true.glb')
M=Model(g); j=g.json; names=[n.get('name') for n in j['nodes']]
i={n:k for k,n in enumerate(names)}
w0=M.world({})
def ang(a,b):
    r=a[:3,:3].T@b[:3,:3]; return np.degrees(np.arccos(np.clip((np.trace(r)-1)/2,-1,1)))
for c in M.clips:
    T=M.clip_times(c); t1=T[-1]
    out={}
    miny=9; rows=[]
    for t in np.arange(0,t1+1e-6,1/30):
        w=M.world(M.sample(c,float(t)))
        rows.append(w)
    for b in ('Bone01','Bone03'):
        base=[r[i['Bip01 Pelvis']] for r in rows]
        out[b]=max(ang(np.linalg.inv(w0[i['Bip01 Pelvis']])@w0[i[b]], np.linalg.inv(bb)@r[i[b]]) for r,bb in zip(rows,base))
    thL=max(ang(np.linalg.inv(w0[i['Bip01 Pelvis']])@w0[i['Bip01 L Thigh']], np.linalg.inv(r[i['Bip01 Pelvis']])@r[i['Bip01 L Thigh']]) for r in rows)
    kn=max(ang(np.linalg.inv(w0[i['Bip01 L Thigh']])@w0[i['Bip01 L Calf']], np.linalg.inv(r[i['Bip01 L Thigh']])@r[i['Bip01 L Calf']]) for r in rows)
    fing=max(ang(np.linalg.inv(w0[i['Bip01 R Hand']])@w0[i['Bip01 R Finger1']], np.linalg.inv(r[i['Bip01 R Hand']])@r[i['Bip01 R Finger1']]) for r in rows)
    hd=max(ang(w0[i['Bip01 Spine3']],w0[i['Bip01 Spine3']]) for r in rows)
    py=[r[i['Bip01 Pelvis']][1,3] for r in rows]; pz=[r[i['Bip01 Pelvis']][2,3] for r in rows]
    fy=[min(r[i['Bip01 L Foot']][1,3],r[i['Bip01 R Foot']][1,3],r[i['Bip01 L Toe0']][1,3],r[i['Bip01 R Toe0']][1,3]) for r in rows]
    print(f'{c:15} {t1:5.2f}s Bone01 {out["Bone01"]:5.1f} Bone03 {out["Bone03"]:5.1f} thighL {thL:5.1f} kneeL {kn:5.1f} finger1R {fing:5.1f} pelvis y {min(py):.2f}..{max(py):.2f} z {min(pz):.2f}..{max(pz):.2f} toe-min {min(fy):.2f}..{max(fy):.2f}')
