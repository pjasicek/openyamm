"""Inspect finger branches in the dense manifold source before local correction."""
import bpy, numpy as np, json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/mv_v2_dense_parts.blend'))
o=bpy.data.objects['P00']; co=np.array([v.co[:] for v in o.data.vertices]); edges=np.array([e.vertices[:] for e in o.data.edges])
for sign in (1,-1):
    wrist=np.array([sign*.49,.0,1.04]); direction=np.array([sign*.55,0,-.835]); depth=(co-wrist)@direction
    hand=(co[:,0]*sign>.40)&(co[:,2]<1.08)&(co[:,2]>.65)
    for cut in (.03,.05,.07,.09,.11,.13,.15):
        keep=hand&(depth>cut); idx=np.where(keep)[0]; adjacency={i:[] for i in idx}
        for a,b in edges[keep[edges[:,0]]&keep[edges[:,1]]]: adjacency[a].append(b); adjacency[b].append(a)
        seen=set(); components=[]
        for i in idx:
            if i in seen: continue
            stack=[i]; c=[]
            while stack:
                v=stack.pop()
                if v in seen: continue
                seen.add(v); c.append(v); stack.extend(adjacency[v])
            if len(c)>20:
                a=co[c]; components.append({'n':len(c),'center':np.round(a.mean(0),4).tolist(),'min':np.round(a.min(0),4).tolist(),'max':np.round(a.max(0),4).tolist()})
        print('CUT',sign,cut,json.dumps(components))
