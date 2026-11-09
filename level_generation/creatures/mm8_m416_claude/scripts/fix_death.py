"""Align the fall's initial heading and retain the guarded crossbow arm during collapse."""
from pathlib import Path
import bpy,json,math,numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped_source.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[p.name for p in r.pose.bones]
def setact(a):
 r.animation_data.action=a
 if a.slots:r.animation_data.action_slot=a.slots[0]
def snap():return {n:r.pose.bones[n].matrix_basis.copy() for n in names}
def forward():
 d=r.pose.bones['B_Spine2'].matrix.to_3x3()@r.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0));return math.atan2(d.y,d.x)
setact(bpy.data.actions['Standing']);sc.frame_set(0);ST=snap();yaw=forward();old=bpy.data.actions['Death'];setact(old);sc.frame_set(6);dy=(yaw-forward()+math.pi)%(2*math.pi)-math.pi;print('DEATH HEADING',math.degrees(dy),flush=True)
rest=r.data.bones['B_Pelvis'].matrix_local;cor=rest.inverted()@Matrix.Rotation(dy,4,'Z')@rest;poses=[]
for f in range(6,int(old.frame_range[1])+1):
 sc.frame_set(f);pose=snap();M=pose['B_Pelvis'].copy();T=M.translation.copy();M=cor@M;M.translation=T;pose['B_Pelvis']=M
 for n in names:
  if n.startswith('B_R_') and any(x in n for x in ['Clavicle','UpperArm','Forearm','Hand','Finger']):w=max(0,min(1,(f-12)/12));w=w*w*(3-2*w);pose[n]=ST[n].lerp(pose[n],w)
 poses.append(pose)
def smooth(x):return x*x*(3-2*x)
poses=[{n:ST[n].lerp(poses[0][n],smooth(i/12)) for n in names} for i in range(12)]+poses
r.animation_data.action=None;bpy.data.actions.remove(old);a=bpy.data.actions.new('Death');a.use_fake_user=True;setact(a);prev={}
for f,pose in enumerate(poses):
 for n,M in pose.items():
  b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.matrix_basis=M;q=b.rotation_quaternion.copy()
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f);b.keyframe_insert('scale',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
for la in a.layers:
 for st in la.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None;(P/'work/death_heading.json').write_text(json.dumps({'initial_yaw_correction_degrees':math.degrees(dy),'duration_s':a.frame_end/30,'right_arm':'Standing guard retained relative to falling torso'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'))
