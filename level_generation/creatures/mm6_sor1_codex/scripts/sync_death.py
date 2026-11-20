import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/robe_motion.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Death'])
with bpy.data.libraries.load(str(p/'work/motion_twist.blend'),link=False) as (a,b):b.actions=['Death']
b.actions[0].use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/robe_sync.blend'))
