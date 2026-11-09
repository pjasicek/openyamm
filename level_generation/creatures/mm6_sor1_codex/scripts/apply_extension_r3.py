import bpy,json,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];keys=json.loads((p/'work/round3_extension_keys.json').read_text())
for path in ['work/round3_motion.blend',*[f'work/round3_lod{n}.blend' for n in range(4)]]:
 bpy.ops.wm.open_mainfile(filepath=str(p/path));rig=bpy.data.objects['Rig'];act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,d in enumerate(keys):
  for n,(loc,rot,scale) in d.items():
   pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=rot;pb.scale=scale
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=n)
 runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));bpy.ops.wm.save_as_mainfile(filepath=str(p/path))
