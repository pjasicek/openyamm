import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for path in [P/f'work/final_lod{i}.blend'for i in range(4)]+[P/'export/mm6_natf.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(path))
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/accepted_master.blend'))as(src,dst):dst.actions=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
 for a in dst.actions:a.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
