"""Give the running blade a little more clearance from the face and the free hand."""
from pathlib import Path
import bpy, math, runpy
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];out=p/'review/motion_options'
bpy.ops.wm.open_mainfile(filepath=str(out/'ogre_motion_options.blend'))
rig=bpy.data.objects['Rig'];axis=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
assert not bpy.context.scene.get('motion_run_extra_clearance'), 'This one-time correction is already applied'
for name in ['Running_Weighted','Running_SlowJog']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);pb=rig.pose.bones['B_R_UpperArm'];h=pb.head.copy()
  forward=rig.pose.bones['B_Spine2'].matrix.to_3x3()@axis
  pb.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(-4),4,forward)@Matrix.Translation(-h)@pb.matrix
  pb.scale=(1,1,1);rows.append(pb.rotation_quaternion.copy())
 for f,q in enumerate(rows):
  pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.context.scene['motion_run_extra_clearance']=4
bpy.ops.wm.save_as_mainfile(filepath=str(out/'ogre_motion_options.blend'))
runpy.run_path(str(p/'scripts/finish_motion_preview.py'),run_name='__main__')
