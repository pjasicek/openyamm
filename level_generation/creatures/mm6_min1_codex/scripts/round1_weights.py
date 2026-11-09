"""Keep elbow influences in the elbow band and continuous weights across its small triangles."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_sources.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in b.vertex_groups];idx={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
for s in 'RL':
 U,F=[np.array(r.data.bones[f'B_{s}_{n}'].head_local) for n in ['UpperArm','Forearm']];d=F-U;t=(co-U)@d/(d@d);allow=np.clip((t-.78)/.30,0,1);fc=[idx[f'B_{s}_Forearm'],idx[f'B_{s}_ForearmTwist']];removed=W[:,fc].sum(1)*(1-allow);W[:,fc]*=allow[:,None];W[:,idx[f'B_{s}_UpperArm']]+=removed
nb=[[] for _ in co]
for e in me.edges:
 a,c=e.vertices
 if pv[a]==0 and pv[c]==0:nb[a].append(c);nb[c].append(a)
hand=[i for i,n in enumerate(names) if 'Hand' in n or 'Finger' in n];arm=[i for i,n in enumerate(names) if 'UpperArm' in n or 'Forearm' in n];band=(pv==0)&(co[:,2]>.98)&(co[:,2]<1.52)&(W[:,hand].sum(1)<.1)&(W[:,arm].sum(1)>.08)
for _ in range(80):
 out=W.copy()
 for i in np.where(band)[0]:
  if nb[i]:out[i]=.65*W[i]+.35*W[nb[i]].mean(0)
 W=out
for i in range(len(co)):
 keep=np.argsort(W[i])[-8:];total=W[i,keep].sum();assert total>0
 for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([i])
 for k in keep:
  if W[i,k]>1e-6:b.vertex_groups[int(k)].add([i],float(W[i,k]/total),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_weighted_sources.blend'));print('CONTINUOUS_WEIGHT_BAND',int(band.sum()))
