import bpy,json
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/repaired_master')
s=bpy.data.scenes['MM6 Goblin Restart - Repaired Master'];bpy.context.window.scene=s
for o in bpy.context.view_layer.objects:o.select_set(o.type=='MESH')
bpy.context.view_layer.objects.active=next(o for o in s.objects if o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'mm6_goblin_repaired_master.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_skins=False,export_apply=True)
print('Exported the repaired master only; original sources preserved')
