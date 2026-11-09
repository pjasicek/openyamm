"""Carry the reviewed surface-fit curls into every held pose, retaining the native death release."""
import bpy,json,math
from pathlib import Path
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_motion.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.load(open(p/('work/grip_pose_'+s+'.json'))) for s in 'RL'}
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
old={n:rig.pose.bones[n].rotation_quaternion.copy() for s in G for n in G[s]['finger_local']};new={n:Quaternion(q) for s in G for n,q in G[s]['finger_local'].items()}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];keys=[]
 for i in range(round(float(act.frame_range[1])*4)+1):
  f=i/4;sc.frame_set(int(f),subframe=f%1);pose={}
  for n,q in new.items():
   t=max(0,min(1,(f-3)/6)) if act.name=='Death' and n.startswith('B_L_') else 1 if act.name=='Dead' and n.startswith('B_L_') else 0
   t=t*t*(3-2*t);delta=(q@old[n].inverted()).slerp(Quaternion(),t);pose[n]=delta@rig.pose.bones[n].rotation_quaternion
  keys.append(pose)
 prev={}
 for i,pose in enumerate(keys):
  for n,q in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i/4)
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_motion.blend'))
