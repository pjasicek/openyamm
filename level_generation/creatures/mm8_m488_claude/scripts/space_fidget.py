from pathlib import Path
import bpy,sys,math
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animated_fixed.blend'))
rig=bpy.data.objects['Rig'];act=bpy.data.actions['Fidget']
if not act.get('m488_arm_spacing'):
 poses=[];last=int(act.frame_range[1]);fwd=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
 for f in range(last+1):
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(f);rig.animation_data.action=None
  t=min(1,f/6,(last-f)/6);t=t*t*(3-2*t);axis=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@fwd).normalized()
  for side,sign in (('L',1),('R',-1)):
   pb=rig.pose.bones['B_'+side+'_UpperArm'];M=pb.matrix.copy();tr=M.translation.copy();M=Matrix.Rotation(sign*math.radians(4)*t,4,axis)@M;M.translation=tr;pb.matrix=M;bpy.context.view_layer.update()
  poses.append({s:rig.pose.bones['B_'+s+'_UpperArm'].rotation_quaternion.copy() for s in 'LR'})
 rig.animation_data.action=act;prev={}
 for f,pose in enumerate(poses):
  for side,q in pose.items():
   if side in prev and q.dot(prev[side])<0:q=-q
   prev[side]=q;pb=rig.pose.bones['B_'+side+'_UpperArm'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 act['m488_arm_spacing']=4;rig.animation_data.action=None
 bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animated_fixed.blend'))
