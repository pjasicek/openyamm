import sys
import numpy as np
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
g=Glb('level_generation/creatures/mm9_ghoul_claude/source/g1/ghoul1_true.glb')
j=g.json
m=j['meshes'][0]['primitives'][0]
pos=g.accessor(m['attributes']['POSITION']); jn=g.accessor(m['attributes']['JOINTS_0']).astype(int); wt=g.accessor(m['attributes']['WEIGHTS_0'])
sk=j['skins'][0]['joints']; names=[j['nodes'][i].get('name') for i in sk]
print(len(pos), len(j['meshes']), len(j['meshes'][0]['primitives']))
for b in ('Bone01','Bone03'):
    if b in names:
        ix=names.index(b); s=((jn==ix)*(wt>0.01)).any(1); print(b, s.sum(), pos[s].min(0) if s.any() else None, pos[s].max(0) if s.any() else None, wt[(jn==ix)][wt[(jn==ix)]>0.01].mean() if s.any() else 0)
    else: print(b,'not in skin')
import collections
c=collections.Counter()
for v in range(len(pos)):
    for k in range(4):
        if wt[v,k]>0.01: c[names[jn[v,k]]]+=1
print(sorted(c.items(), key=lambda x:-x[1]))
# per-clip rotation of Bone01/03/fingers
M=Model(g); print(M.clips.keys() if hasattr(M.clips,'keys') else M.clips)
