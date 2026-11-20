from pathlib import Path
import bpy,sys
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v2c.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ['Standing','Walking','Fidget']:
 act=bpy.data.actions[name];poses=[]
 for f in range(int(act.frame_range[1])+1):
  rig.animation_data.action=act
  if len(act.slots):rig.animation_data.action_slot=act.slots[0]
  sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};ch=armik.W(rig,'B_Spine2')
  if f==0:C0=ch.copy();own0=armik.W(rig,'B_L_Hand').translation.copy()
  target=ch@(C0.inverted()@Vector((.30,-.20,1.07)))+(armik.W(rig,'B_L_Hand').translation-own0)*.15
  rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis=snap[b.name]
  armik.solve(rig,'L',target,pole=(.45,.05,1.13))
  # A relaxed wrist continues the forearm; its rest offset already contains the measured palm frame.
  rel=rig.data.bones['B_L_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones['B_L_Hand'].matrix_local.to_3x3()
  armik.set_world(rig,'B_L_Hand',armik.rot_world(armik.W(rig,'B_L_Hand'),armik.W(rig,'B_L_Forearm').to_3x3().normalized()@rel))
  poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']})
 rig.animation_data.action=act
 for f,pose in enumerate(poses):
  for n,q in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v2c.blend'))
