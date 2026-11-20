"""Assemble independently measured component reductions without modifying the accepted rig or actions."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';selected=json.loads((R/'curve.json').read_text())['selected']
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'))
 for part in ['Body','Axe','Shield']:
  tag=selected[f'{part}_LOD{level}'];obj=bpy.data.objects[part]
  with bpy.data.libraries.load(str(R/'candidates'/f'{tag}.blend'),link=False) as (src,dst):dst.meshes=[part+'_reduction_mesh']
  obj.data=dst.meshes[0];assert obj.data
  for o in bpy.data.objects:o.select_set(o==obj)
  bpy.context.view_layer.objects.active=obj
  bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 bpy.ops.wm.save_as_mainfile(filepath=str(R/f'lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'))
