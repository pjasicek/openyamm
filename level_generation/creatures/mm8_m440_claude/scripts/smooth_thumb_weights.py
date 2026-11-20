"""Blend the thumb's metacarpal and knuckle weights through its web, preserving the distal tip."""
from pathlib import Path
import bpy,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_fingers.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
for side,part in [('R',2),('L',3)]:
 cols=[i for i,n in enumerate(names) if n==f'B_{side}_Hand' or n.startswith(f'B_{side}_Finger0')]
 edges=np.array([tuple(e.vertices) for e in me.edges if all(pv[v]==part for v in e.vertices)])
 C=W[:,cols].copy();total=C.sum(1);band=(pv==part)&(total>.95)&~((co[:,2]<.672)&(np.abs(co[:,0])<.46))
 for _ in range(18):
  sums=C.copy();degree=np.ones(len(co));np.add.at(sums,edges[:,0],C[edges[:,1]]);np.add.at(sums,edges[:,1],C[edges[:,0]]);np.add.at(degree,edges[:,0],1);np.add.at(degree,edges[:,1],1)
  avg=sums/degree[:,None];avg/=np.maximum(avg.sum(1,keepdims=True),1e-9)
  C[band]=.5*C[band]+.5*avg[band]*total[band,None]
 W[:,cols]=C
assert np.allclose(W.sum(1),1,atol=2e-4)
for v in me.vertices:
 for e in list(v.groups):body.vertex_groups[e.group].remove([v.index])
 for j in np.flatnonzero(W[v.index]>1e-5):body.vertex_groups[int(j)].add([v.index],float(W[v.index,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot_fingers.blend'))
