"""Smooth the shoulder/elbow skin transition after anatomical humeral roll fitting."""
import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_motion.blend'));b=bpy.data.objects['Body'];me=b.data;names=[g.name for g in b.vertex_groups];W=np.zeros((len(me.vertices),len(names)));co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);nb=[[] for _ in co]
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
for e in me.edges:
 a,c=e.vertices
 if pv[a]==0 and pv[c]==0:nb[a].append(c);nb[c].append(a)
hand=[i for i,n in enumerate(names) if 'Hand' in n or 'Finger' in n];arm=[i for i,n in enumerate(names) if 'UpperArm' in n or 'Forearm' in n];band=(pv==0)&(co[:,2]>.98)&(co[:,2]<1.50)&(W[:,hand].sum(1)<.1)&(W[:,arm].sum(1)>.1)
for _ in range(16):
 out=W.copy()
 for i in np.where(band)[0]:
  if nb[i]:out[i]=.75*W[i]+.25*W[nb[i]].mean(0)
 W=out
for i in np.where(band)[0]:
 keep=np.argsort(W[i])[-4:];total=W[i,keep].sum();assert total>0
 for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([int(i)])
 for j in keep:
  if W[i,j]>0:b.vertex_groups[int(j)].add([int(i)],float(W[i,j]/total),'REPLACE')
print('SMOOTHED',int(band.sum()));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_master.blend'))
