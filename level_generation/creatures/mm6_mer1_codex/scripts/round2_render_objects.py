import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_mer1_a.glb'))
for o in bpy.data.objects:
 if o.type=='MESH':print('MESH OBJECT',o.name,o.hide_render,o.hide_get(),o.location[:],len(o.data.polygons),[m.name for m in o.data.materials],flush=True)
