import bpy,json,sys,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from staff_ik import Side
R=Side('R');L=Side('L');G=json.loads((P/'work/grip_pose_left.json').read_text());L.grip_hand=Vector(G['handle_centre_hand_local']);L.axis_hand=Vector(G['handle_axis_hand_local'])
def setact(a):
 rig.animation_data.action=a
 if a:rig.animation_data.action_slot=a.slots[0]
def pose():return {pb.name:(pb.rotation_quaternion.copy(),pb.location.copy())for pb in rig.pose.bones}
def apply(p):
 setact(None)
 for n,(q,l)in p.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
 bpy.context.view_layer.update()
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
poses={}
for role in ['Attack','Cast','Death']:
 a=bpy.data.actions[role];setact(a);poses[role]=[]
 for f in range(int(a.frame_range[1])+1):sc.frame_set(f);poses[role].append(pose())
from arm_path import refine_arm_paths
refine_arm_paths(poses,apply,pose,world,L,R,P)
for role,frames in poses.items():
 setact(bpy.data.actions[role]);prev={}
 for f,p in enumerate(frames):
  for side in 'LR':
   for bone in ['UpperArm','Forearm','Hand']:
    n=f'B_{side}_{bone}';q=p[n][0]
    if n in prev and q.dot(prev[n])<0:q=-q
    prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
from bake_twist import bake_twist
for role in poses:bake_twist(bpy.data.actions[role])
setact(bpy.data.actions['Death']);sc.frame_set(int(bpy.data.actions['Death'].frame_range[1]));end=pose();setact(bpy.data.actions['Dead'])
for f in range(241):
 for n,(q,l)in end.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_master.blend'))
for file in ['production_body','textured_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));bpy.data.objects['Rig'].animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/animated_master.blend'))as(src,dst):dst.actions=src.actions
 for a in dst.actions:a.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'))
runpy.run_path(str(P/'scripts/fit_shoulder_weights.py'),run_name='__main__');runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
