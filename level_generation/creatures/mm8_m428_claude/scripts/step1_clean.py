"""Join the reviewed Smart Topology parts (work/st_v1_parts.blend) into one Body with a per-vertex 'piece' attribute
(part index), drop the 2-triangle stray (P23), keep the original positions in 'orig_co', give a provisional 1x1 clay
texture (Meshy rigging needs a textured GLB) and export export/m428_clean_v1.glb for the auto-rig joint estimate.
Parts: P00 dress/torso/head skin, P01 hidden legs and shoes, P02 hair, P03/P04 left/right forearm+hand, P05 fringe,
P08/P09 eyes, P10/P11 shoulder bands, others lacing, belt, buckle and mouth pieces."""
import bpy, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/st_v1_parts.blend'))
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name == 'P23':
        bpy.data.objects.remove(o, do_unlink=True)
parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('P')]
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    a = o.data.attributes.new('piece', 'INT', 'POINT')
    a.data.foreach_set('value', [int(o.name[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['P00']
bpy.ops.object.join()
body = bpy.context.object
body.name = body.data.name = 'Body'
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set(
    'vector', [c for v in body.data.vertices for c in v.co])
mat = bpy.data.materials.new('Provisional clay for rigging'); mat.use_nodes = True
im = bpy.data.images.new('Provisional_clay', width=1, height=1, alpha=True); im.pixels = [0.55, 0.55, 0.55, 1.0]; im.pack()
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = im
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:
    body.data.uv_layers.new(name='ProvisionalUV')
for p in body.data.polygons:
    p.material_index = 0; p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/step1.blend'))
(P / 'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P / 'export/m428_clean_v1.glb'), export_format='GLB', use_selection=True,
                          export_animations=False, export_yup=True, export_extras=True)
print('RIG_UPLOAD', len(body.data.vertices), sum(len(p.vertices) - 2 for p in body.data.polygons))
