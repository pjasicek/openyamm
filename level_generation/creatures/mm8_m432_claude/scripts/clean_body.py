"""Repair the damaged left pauldron/glove from their intact symmetric counterparts."""
import json
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
sys.dont_write_bytecode = True
import common

bpy.ops.wm.open_mainfile(filepath=str(P / 'work/st_v1_parts.blend'))
removed = []
for obj in list(bpy.data.objects):
    if obj.type != 'MESH':
        bpy.data.objects.remove(obj, do_unlink=True)
        continue
    co = np.array([v.co[:] for v in obj.data.vertices])
    wrist_fragment = len(obj.data.polygons) < 20 and co[:, 0].min() > 0.50 and co[:, 2].max() < 1.18
    if obj.name in ('P06', 'P08') or wrist_fragment:
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

for original, replacement in [('P05', 'P06'), ('P07', 'P08')]:
    source = bpy.data.objects[original]
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = replacement
    bpy.context.scene.collection.objects.link(obj)
    obj.data.transform(Matrix.Diagonal((-1, 1, 1, 1)))
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()

# The returned left forearm is also displaced in depth; restore the symmetric sleeve to meet its repaired glove.
core = bpy.data.objects['P00']
bm = bmesh.new()
bm.from_mesh(core.data)
bmesh.ops.symmetrize(bm, input=list(bm.verts) + list(bm.edges) + list(bm.faces), direction='-X', dist=1e-5)
bm.to_mesh(core.data)
bm.free()

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for obj in meshes:
    piece = int(obj.name[1:])
    obj.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [piece] * len(obj.data.vertices))
    obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['P00']
bpy.ops.object.join()
body = bpy.context.object
body.name = body.data.name = 'Body'
co = np.array([v.co[:] for v in body.data.vertices])
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
assert all(np.isfinite(co.ravel())) and abs(co[:, 2].min()) < 1e-5
assert abs(co[:, 2].max() - 1.9) < 1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/body_clean.blend'))
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(str(P / 'review/clean'), 0.95, 2.15,
                    views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
for side, x in [('right', -0.61), ('left', 0.61)]:
    common.render_views(str(P / f'review/clean_hand_{side}'), 1.06, 0.25,
                        views=('front', 'back'), resolution=(600, 600), target=(x, -0.05))

# This flat atlas only makes anatomy readable to the joint estimator; final textures come after weighting.
colors = [(0.10, 0.10, 0.11, 1), (0.35, 0.16, 0.12, 1), (0.72, 0.72, 0.74, 1), (0.5, 0.35, 0.12, 1)]
im = bpy.data.images.new('Provisional_anatomy', width=128, height=32, alpha=True)
im.pixels = [c for _y in range(32) for x in range(128) for c in colors[x // 32]]
im.filepath_raw = str(P / 'work/provisional_anatomy.png')
im.file_format = 'PNG'
im.save()
mat = bpy.data.materials.new('Provisional_anatomy')
mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = im
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 0.8
body.data.materials.clear()
body.data.materials.append(mat)
uv = body.data.uv_layers.new(name='ProvisionalUV')
piece = body.data.attributes['piece'].data
for face in body.data.polygons:
    part = piece[face.vertices[0]].value
    region = 1 if part == 1 else 2 if part in (2, 11) else 3 if part >= 12 else 0
    for loop in face.loop_indices:
        uv.data[loop].uv = ((region + 0.5) / 4, 0.5)
    face.material_index = 0
for obj in bpy.data.objects:
    obj.select_set(obj == body)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=str(P / 'work/body_for_rig.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False,
                          export_attributes=False, export_yup=True)
report = {'removed_corrupt_parts': removed, 'mirrored_pairs': {'P05': 'P06', 'P07': 'P08'},
          'vertices': len(body.data.vertices), 'triangles': sum(len(f.vertices) - 2 for f in body.data.polygons),
          'height_m': 1.9, 'provisional_texture_only': True}
(P / 'work/body_cleanup.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
