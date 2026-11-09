"""Anatomical ownership for the minotaur's shells and integrated bracers."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2t.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];idx={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
J=lambda n:np.array(rig.data.bones[n].head_local)
# Clear arm influence on the medial torso; retain a broad shoulder transition.
for side in ['L','R']:
 shoulder=J(f'B_{side}_UpperArm');sgn=1 if side=='L' else -1;arm=[idx[n] for n in names if n.startswith(f'B_{side}_') and any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]
 elbow=J(f'B_{side}_Forearm');fade=np.clip((co[:,0]*sgn-.24)/.075,0,1);removed=W[:,arm].sum(1)*(1-fade);W[:,arm]*=fade[:,None];upper=np.clip((co[:,2]-1.30)/.12,0,1);W[:,idx[f'B_{side}_Clavicle']]+=removed*upper;W[:,idx['B_Spine1']]+=removed*(1-upper)
 # Inner elbow skin moves with the limb; a torso fraction there tears during flexion.
 own=np.clip((co[:,0]*sgn-.28)/.055,0,1)*np.clip((1.37-co[:,2])/.10,0,1)
 trunk=[idx[n] for n in names if n in ['B_Spine','B_Spine1','B_Spine2',f'B_{side}_Clavicle']]
 moved=W[:,trunk].sum(1)*own;W[:,trunk]*=(1-own[:,None]);mix=np.clip((co[:,2]-elbow[2]+.04)/.10,0,1);W[:,idx[f'B_{side}_UpperArm']]+=moved*mix;W[:,idx[f'B_{side}_Forearm']]+=moved*(1-mix)

# Head, jaw, ears, nose ring and mane must never follow a shrugging shoulder.
jaw=1.58+.25*(co[:,1]+.03)
head=(co[:,2]>1.66)|((co[:,2]>jaw)&(co[:,1]<.07)&(np.abs(co[:,0])<.20))|np.isin(pv,[4,8,9]);W[head]=0;W[head,idx['B_Head']]=1
# Posterior trapezius is torso, not jaw. Remove the old rigid-head cliff across the shoulder.
a=np.clip((np.abs(co[:,0])-.12)/.10,0,1)*np.clip((1.65-co[:,2])/.08,0,1)*np.clip((co[:,1]-.02)/.10,0,1)
for n in ['B_Head','B_Neck']:
 moved=W[:,idx[n]]*a;W[:,idx[n]]-=moved;W[:,idx['B_Spine2']]+=moved
# Neck/chest fittings follow the adjacent body's weights, not the hands.
skin=np.where(pv==0)[0];kd=KDTree(len(skin))
for i,v in enumerate(skin):kd.insert(co[v],i)
kd.balance()
for i in np.where(np.isin(pv,[2,3,5,7,6,11,12,13,14,16]))[0]:
 if pv[i]==6:W[i]=0;W[i,idx['B_Pelvis']]=1
 else:
  hits=kd.find_n(co[i],3);ws=np.array([1/max(h[2],.0001) for h in hits]);W[i]=(W[[skin[h[1]] for h in hits]]*ws[:,None]).sum(0)/ws.sum()
# Cloth follows the adjacent hip/thigh skin, including the anterior leg's lift.
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sf=[tuple(f.vertices) for f in me.polygons if all(pv[i]==0 for i in f.vertices)]
tree=BVHTree.FromPolygons(co.tolist(),sf)
from mathutils.geometry import barycentric_transform
for i in np.where(pv==1)[0]:
 loc,nrm,fi,d=tree.find_nearest(Vector(co[i]))
 ids=list(sf[fi]);a,b,c=[Vector(co[j]) for j in ids];bary=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));W[i]=sum(W[j]*bary[k] for k,j in enumerate(ids))
 if co[i,2]<.97 and d<.10 and (Vector(co[i])-loc).dot(nrm)<.018:me.vertices[i].co=loc+nrm*.018
# Diffuse the auto-rigger's abrupt shoulder/elbow transitions without changing the fingers.
nb=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;nb[a].append(b);nb[b].append(a)
armcols=[idx[n] for n in names if any(k in n for k in ['UpperArm','Forearm'])];handcols=[idx[n] for n in names if 'Hand' in n or 'Finger' in n]
band=(co[:,2]>.98)&(co[:,2]<1.49)&(W[:,handcols].sum(1)<.1)&(pv==0)
for _ in range(20):
 out=W.copy()
 for i in np.where(band)[0]:
  if nb[i]:out[i]=.7*W[i]+.3*W[nb[i]].mean(0)
 W=out
W=np.maximum(W,0);assert np.all(W.sum(1)>0);W/=W.sum(1)[:,None]
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i,w in enumerate(W):
 for j in np.where(w>1e-5)[0]:body.vertex_groups[j].add([i],float(w[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'))
