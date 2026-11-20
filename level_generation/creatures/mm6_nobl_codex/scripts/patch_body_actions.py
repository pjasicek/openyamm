"""Replace body channels only when the cloth parent transforms are unchanged."""
import bpy,sys,os,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'));r=bpy.data.objects['Rig']
def fc(a):return [f for l in a.layers for s in l.strips for b in s.channelbags for f in b.fcurves]
def use(a):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
old={name:bpy.data.actions[name] for name in roles}
with bpy.data.libraries.load(str(p/'work/rig_v6t.blend'),link=False) as (src,dst):dst.actions=list(roles)
for role,new in zip(roles,dst.actions):
 prior=old[role];before=[]
 for a in [prior,new]:
  use(a);poses=[]
  for f in range(int(a.frame_range[1])+1):
   bpy.context.scene.frame_set(f)
   poses.append([np.array(r.pose.bones[n].matrix) for n in ['B_Pelvis','B_Spine2']])
  before.append(np.array(poses))
 err=np.max(abs(before[0]-before[1]))
 assert err<1e-4,(role,err)
 bag=new.layers[0].strips[0].channelbags[0]
 for curve in fc(prior):
  if any(prefix in curve.data_path for prefix in ['Cloak_','Tabard_','BackTabard_']):
   c=bag.fcurves.new(curve.data_path,index=curve.array_index)
   for k in curve.keyframe_points:
    q=c.keyframe_points.insert(k.co.x,k.co.y);q.interpolation=k.interpolation
 prior.name=role+'_superseded';new.name=role;new.use_fake_user=True
 bpy.data.actions.remove(prior)
 print('BODY_PATCH',role,'cloth-parent matrix error',err)
use(bpy.data.actions['Standing'])
bpy.ops.wm.save_mainfile()
