"""Fit broad hips and the corpse club placement without replacing the selected motions."""
import bpy,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_grounded.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
fwd=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
carry={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand']}
for name in ['Walking','Fidget','Death']:
 a=bpy.data.actions[name];poses=[]
 for f in range(int(a.frame_range[1])+1):
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f)
  snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis=snap[b.name]
  if name=='Death' and f<12:
   t=max(0,min(1,f/12));t=t*t*(3-2*t)
   for n,q in carry.items():rig.pose.bones[n].rotation_quaternion=q.slerp(rig.pose.bones[n].rotation_quaternion,t)
  bpy.context.view_layer.update();axis=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@fwd).normalized()
  for sd in ('L','R') if name=='Walking' else ('L',):
   angle=14 if name=='Walking' else 8 if name=='Fidget' else 40*max(0,min(1,(f-14)/10))
   if name=='Death':
    t=max(0,min(1,(f-14)/10));angle=40*t*t*(3-2*t)
   b=rig.pose.bones[f'B_{sd}_UpperArm'];M=b.matrix.copy();pos=M.translation.copy();M=Matrix.Rotation(math.radians(angle if sd=='L' else -angle),4,axis)@M;M.translation=pos;b.matrix=M;bpy.context.view_layer.update()
  poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in (['B_L_UpperArm','B_R_UpperArm']+list(carry))})
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f,qs in enumerate(poses):
  for n,q in qs.items():
   b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
 print('CLEARANCE arm abduction',name)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_clear.blend'))
