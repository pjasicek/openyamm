"""Smooth the short armpit weight gradients exposed by the larger two-hand reach."""
import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion.blend'));body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);groups=[g.name for g in body.vertex_groups];w=np.zeros((len(co),len(groups)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
old=w.copy();ids=np.where((pv==1)&(co[:,0]>.06)&(co[:,0]<.27)&(co[:,2]>1.13)&(co[:,2]<1.40))[0]
armcols=[i for i,n in enumerate(groups) if n.startswith('B_L_') and any(k in n for k in ['UpperArm','Forearm'])];chest=groups.index('B_Spine2')
for i in ids:
 x,y,z=co[i];chest_side=1-np.clip((x-.15)/.10,0,1);height=np.clip((z-1.13)/.05,0,1)*np.clip((1.40-z)/.06,0,1);removed=w[i,armcols]*chest_side*height;w[i,armcols]-=removed;w[i,chest]+=removed.sum()
for i in ids:
 for g in body.vertex_groups:g.remove([int(i)])
 order=np.argsort(w[i])[-8:];vals=w[i,order];vals/=vals.sum()
 for j,x in zip(order,vals):
  if x>1e-8:body.vertex_groups[int(j)].add([int(i)],float(x),'REPLACE')
assert max(abs(sum(g.weight for g in v.groups)-1) for v in me.vertices)<1e-5
(p/'work/round3_weight_repair.json').write_text(json.dumps({'vertices':len(ids),'max_weight_change':float(abs(w-old).max()),'region':'left robe armpit, face/collar/hands unchanged','method':'torso-side underarm follows chest; transition across 10 cm to the sleeve; eight normalized influences'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_weighted.blend'))
