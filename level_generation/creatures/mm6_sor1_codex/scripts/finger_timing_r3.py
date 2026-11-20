import bpy,json,runpy
from pathlib import Path
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];L=json.loads((p/'work/round2_left_grip.json').read_text())
def smooth(x):
 x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
for path in ['work/round3_motion.blend',*[f'work/round3_lod{n}.blend' for n in range(4)]]:
 bpy.ops.wm.open_mainfile(filepath=str(p/path));rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0);stand={n:rig.pose.bones[n].rotation_quaternion.copy() for n in L['fingers']};act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f in range(301):
  close=smooth((f-94)/24)*smooth((201-f)/24)
  for n,q in L['fingers'].items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=stand[n].slerp(Quaternion(q),close);pb.keyframe_insert('rotation_quaternion',frame=f)
 runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));bpy.ops.wm.save_as_mainfile(filepath=str(p/path))
