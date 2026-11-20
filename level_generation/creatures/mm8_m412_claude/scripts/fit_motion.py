"""Fit the selected Hit to the standing base and confine death travel; preserve world upper-body motion."""
import bpy,sys,math,numpy as np
from mathutils import Matrix,Vector
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_runfit.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[b.name for b in rig.data.bones];legs=[n for n in names if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]
def act(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);sc.frame_set(f);return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 act(None)
 for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
def write(n,poses):
 bpy.data.actions.remove(bpy.data.actions[n]);a=bpy.data.actions.new(n);a.use_fake_user=True;act(a)
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
st=sample(bpy.data.actions['Standing'],0);stpel=rig.pose.bones['B_Pelvis'].matrix.copy()
a=bpy.data.actions['Hit'];poses=[]
for f in range(int(a.frame_range[1])+1):
 pose=sample(a,f);world={n:rig.pose.bones[n].matrix.to_3x3().copy() for n in names}
 pose['B_Pelvis']=st['B_Pelvis']
 for n in legs:pose[n]=st[n]
 apply(pose)
 for n in names:
  if n in legs or n=='B_Pelvis':continue
  m=world[n].to_4x4();m.translation=rig.pose.bones[n].head;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
 poses.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
write('Hit',poses)
a=bpy.data.actions['Death'];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
# Horizontal pelvis travel is limited; vertical collapse and the backward fall remain from the source.
rest=rig.data.bones['B_Pelvis'].matrix_local
for pose in poses:
 q,l=pose['B_Pelvis'];d=rest.to_3x3()@l;d.x*=0.35;d.y*=0.35;pose['B_Pelvis']=(q,rest.to_3x3().inverted()@d)
write('Death',poses);act(None)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_fitted.blend'))
