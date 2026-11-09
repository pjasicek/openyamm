"""Wing retexture upload v3b from the restored runtime layout of work/v3/uv_master.blend (no repacking): the wing
islands at their runtime place in [0, .86]^2, the body and head sets scaled into the 0.14 squares beside them, as
the v3a upload. Out: work/v3/wings_upload_b.glb"""
import bpy
from pathlib import Path
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
dup = o.copy(); dup.data = o.data.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear(); bpy.context.collection.objects.link(dup)
for l in [l for l in dup.data.uv_layers if l.name != 'UVMap']: dup.data.uv_layers.remove(l)
uv = dup.data.uv_layers['UVMap'].data
place = {0: (.14 / .92, .86, 0), 1: (.14 / .86, .86, .14), 2: (1, 0, 0)}
for f in dup.data.polygons:
    s, ox, oy = place[f.material_index]
    for li in f.loop_indices:
        u, v = uv[li].uv; uv[li].uv = (ox + u * s, oy + v * s)
dup.data.materials.clear(); m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
for f in dup.data.polygons: f.material_index = 0
bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=str(P / 'work/v3/wings_upload_b.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_attributes=False, export_morph=False)
print('UPLOAD written')
