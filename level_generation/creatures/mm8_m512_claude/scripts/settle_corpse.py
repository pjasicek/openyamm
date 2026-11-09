"""Settle the raised-side legs during the last collapse, keeping the retained UV master intact."""
import bpy,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(P/'work/wolf_uv_repaired.blend'))
rig=bpy.data.objects['Wolf_Rig'];mesh=bpy.data.objects['Wolf'];sc=bpy.context.scene
for name,frames in [('Death',15),('Dead',24)]:
 original=bpy.data.actions[name];poses=[]
 for frame in range(frames+1):
  rig.animation_data.action=original;sc.frame_set(frame+1);bpy.context.view_layer.update()
  rig.animation_data.action=None
  u=1 if name=='Dead' else max(0,min(1,(frame/24-.3)/(.625-.3)))
  u=u*u*(3-2*u)
  for side,angle in [('R',-65),('L',-10)]:
   for bone in ['UpperArm','Thigh']:posing.rotate_world(rig,f'{bone}_{side}','Y',angle*u)
  posing.rotate_world(rig,'Tail1','Y',-20*u)
  ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all()
  root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(Vector((0,0,(.003-co[:,2].min())*u)))@root.matrix
  bpy.context.view_layer.update()
  poses.append({b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones})
 bpy.data.actions.remove(original)
 action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action;prev={}
 for frame,data in enumerate(poses,1):
  for b in rig.pose.bones:
   loc,q=data[b.name]
   if b.name in prev and prev[b.name].dot(q)<0:q=-q
   prev[b.name]=q;b.location=loc;b.rotation_quaternion=q;b.scale=(1,1,1)
   for channel in ['location','rotation_quaternion','scale']:b.keyframe_insert(channel,frame=frame)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/wolf_uv_settled.blend'))
