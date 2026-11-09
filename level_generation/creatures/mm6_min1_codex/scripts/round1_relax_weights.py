"""Diffuse by physical edge length so millimetre triangles do not carry centimetre weight jumps."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_contacts.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in b.vertex_groups];idx={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
nb=[[] for _ in co]
for e in me.edges:
 a,c=e.vertices
 if pv[a]==0 and pv[c]==0:nb[a].append(c);nb[c].append(a)
hand=[i for i,n in enumerate(names) if 'Hand' in n or 'Finger' in n];band=(pv==0)&(co[:,2]>.98)&(co[:,2]<1.60)&(W[:,hand].sum(1)<.1)&(W[:,idx['B_Head']]<.2);ids=np.where(band)[0];dist={i:1/np.maximum(np.linalg.norm(co[nb[i]]-co[i],axis=1),.001)**2 for i in ids if nb[i]}
for _ in range(100):
 out=W.copy()
 for i,d in dist.items():out[i]=.5*W[i]+.5*(W[nb[i]]*d[:,None]).sum(0)/d.sum()
 W=out
for s in 'RL':
 U,F=[np.array(r.data.bones[f'B_{s}_{n}'].head_local) for n in ['UpperArm','Forearm']];d=F-U;t=(co-U)@d/(d@d);allow=np.clip((t-.65)/.45,0,1);fc=[idx[f'B_{s}_Forearm'],idx[f'B_{s}_ForearmTwist']];removed=W[:,fc].sum(1)*(1-allow);W[:,fc]*=allow[:,None];W[:,idx[f'B_{s}_UpperArm']]+=removed
for i in range(len(W)):
 keep=np.argsort(W[i])[-8:];total=W[i,keep].sum();assert total>0
 for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([i])
 for k in keep:
  if W[i,k]>1e-7:b.vertex_groups[int(k)].add([i],float(W[i,k]/total),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_relaxed.blend'));print('EDGE_LENGTH_DIFFUSION',len(ids))
