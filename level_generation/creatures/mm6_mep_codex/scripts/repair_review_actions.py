import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for level in [1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(p/f'work/final_lod{level}.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(p/'export/mm6_mep.blend'),link=False) as (source,target):target.actions=list(source.actions)
 for a in bpy.data.actions:a.use_fake_user=True
 assert len(bpy.data.actions)==9
 bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/final_lod{level}.blend'))
