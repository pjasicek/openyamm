"""Remove pole acceleration while retaining library hand orientation and a pure elbow hinge."""
import bpy,sys,math,numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from arm_ik import swing_twist_deg
def average(qs,f,sigma):
 q0=qs[f];v=np.zeros(4)
 for k in range(max(0,f-6),min(len(qs),f+7)):
  q=qs[k];v+=np.array(q if q.dot(q0)>=0 else -q)*math.exp(-.5*((k-f)/sigma)**2)
 return Quaternion(v).normalized()
for role in ['Death']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];poses=[];wr=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);poses.append({b.name:(b.location.copy(),b.rotation_quaternion.copy())for b in rig.pose.bones});wr.append({sd:rig.pose.bones[f'B_{sd}_Hand'].matrix.to_quaternion()for sd in 'LR'})
 for sd in 'LR':
  qs=[q[sd]for q in wr]
  for f in range(len(wr)):wr[f][sd]=average(qs,f,1.3)
 old=[p.copy()for p in poses]
 for sd in ('R'if role=='Attack'else'LR'):
  for part in ['UpperArm','Forearm']:
   name=f'B_{sd}_{part}';qs=[p[name][1]for p in old]
   for f in range(len(poses)):poses[f][name]=(old[f][name][0],average(qs,f,2.5 if role=='Attack'else 1.3))
 rig.animation_data.action=None
 for f,p in enumerate(poses):
  for name,(l,q)in p.items():b=rig.pose.bones[name];b.location=l;b.rotation_quaternion=q
  bpy.context.view_layer.update()
  for sd in 'LR':
   hand=rig.pose.bones[f'B_{sd}_Hand'];M=wr[f][sd].to_matrix().to_4x4();M.translation=hand.head;hand.matrix=M;bpy.context.view_layer.update()
   fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];ub=rig.data.bones[f'B_{sd}_UpperArm'];seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=swing_twist_deg(rel@rr.inverted(),seg)[1]
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(seg,math.radians(max(-85,min(85,.65*tw))));ax=(ub.matrix_local.inverted()@fb.head_local).normalized();uw=swing_twist_deg(rig.pose.bones[ub.name].rotation_quaternion,ax)[1];rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*uw))
  poses[f]={b.name:(b.location.copy(),b.rotation_quaternion.copy())for b in rig.pose.bones}
 bpy.data.actions.remove(a);a=bpy.data.actions.new(role);a.use_fake_user=True;rig.animation_data.action=a;prev={}
 for f,pose in enumerate(poses):
  for name,(l,q)in pose.items():
   if name in prev and q.dot(prev[name])<0:q=-q
   prev[name]=q;pb=rig.pose.bones[name];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if name=='B_Pelvis'or name.startswith('Cloth'):pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_precloth.blend'))
