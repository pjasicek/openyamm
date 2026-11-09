"""work/v3/uv_master.blend (graft, spines, v3 UVs) + cdr1 rig -> work/v3/geom_export.glb: skinned geometry only
(4 influences, no clips, no images) for swap_lod0.py. Material slots carry the installed names
(DragonBody_A / DragonHead_A / DragonWings_A) so swap_lod0 matches the primitives."""
import bpy
from pathlib import Path
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for i, name in enumerate(['DragonBody_A', 'DragonHead_A', 'DragonWings_A']):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); body.data.materials[i] = m
for l in [l for l in body.data.uv_layers if l.name != 'UVMap']: body.data.uv_layers.remove(l)
body.data.uv_layers.active = body.data.uv_layers['UVMap']
print('MATERIALS', [m.name for m in body.data.materials])
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(P / 'work/v3/geom_export.glb'), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in body.data.polygons))
