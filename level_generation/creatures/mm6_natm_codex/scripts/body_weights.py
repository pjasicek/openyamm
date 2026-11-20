"""Make native feather shells follow their anatomical owner; strip stray skin influence."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_twist.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);names=[g.name for g in ob.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-12);skin=np.where(pv==0)[0]
# The source has open shoulders: fade arm ownership medially, keeping neck and chest on their own chain.
for sd in 'LR':
 sh=np.array(rig.data.bones[f'B_{sd}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{sd}_Clavicle'].head_local);d=(sh-cl)/np.linalg.norm(sh-cl);medial=(co-sh)@d;keep=np.clip(1+medial/.075,0,1)
 for n in [f'B_{sd}_UpperArm',f'B_{sd}_UpperArmTwist']:
  lost=W[skin,gi[n]]*(1-keep[skin]);W[skin,gi[n]]-=lost;W[skin,gi['B_Spine2']]+=lost
for i in skin:
 if co[i,2]>1.47:
  t=float(np.clip((co[i,2]-1.47)/.055,0,1));W[i]=0;W[i,gi['B_Neck']]=1-t;W[i,gi['B_Head']]=t
kd=KDTree(len(skin))
for j,i in enumerate(skin):kd.insert(co[i],j)
kd.balance();parts={}
for part in sorted(set(pv.tolist())-{0}):
 ids=np.where(pv==part)[0];c=co[ids].mean(0);sd='L' if c[0]>0 else 'R'
 if part in (2,3):n='B_Head'
 elif part in (1,10):
  # Narrow centre loincloth panels; local secondary bones are added with the final motions.
  for i in ids:
   t=float(np.clip((1.01-co[i,2])/.35,0,1))*.25;W[i]=0;W[i,gi['B_Pelvis']]=1-t;W[i,gi['B_L_Thigh']]=t/2;W[i,gi['B_R_Thigh']]=t/2
  parts[part]='loincloth';continue
 elif c[2]<.45:n=f'B_{sd}_Calf'
 elif c[2]<1.07:n='B_Pelvis'
 elif abs(c[0])>.20 and 1.13<c[2]<1.29:n=f'B_{sd}_UpperArm'
 elif c[2]>1.29:n='B_Spine2'
 else:n='B_Spine1'
 # Feathers stay rigid individually; the mantle remains attached to the back.
 W[ids]=0;W[ids,gi[n]]=1;parts[part]=n
for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
for n in names:ob.vertex_groups.new(name=n)
for i,w in enumerate(W):
 ids=np.argsort(w)[-4:];v=w[ids];v/=v.sum()
 for j,a in zip(ids,v):
  if a>1e-8:ob.vertex_groups[int(j)].add([i],float(a),'REPLACE')
 assert abs(sum(e.weight for e in me.vertices[i].groups)-1)<1e-6
(P/'work/part_owners.json').write_text(json.dumps(parts,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
