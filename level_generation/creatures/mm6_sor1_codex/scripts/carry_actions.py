import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_fingers.blend'))
with bpy.data.libraries.load(str(p/'work/motion_base.blend'),link=False) as (a,b):b.actions=[n for n in a.actions if n in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']]
for a in b.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_clean.blend'))
