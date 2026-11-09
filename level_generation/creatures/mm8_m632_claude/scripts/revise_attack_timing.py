"""Retiming-only update: keep the reviewed pose path, mesh and seven other actions."""
import bpy,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/finish_motion.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
bpy.data.actions.remove(bpy.data.actions['Attack'])
with bpy.data.libraries.load(str(P/'work/motion_timed.blend'),link=False) as (src,dst):
 dst.actions=['Attack']
dst.actions[0].use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
