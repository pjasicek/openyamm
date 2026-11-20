"""Step 2 (after hes_turrets_claude/scripts/prepare_uv.py): reduce, shade and unwrap the split Harvester; the neutral
upload for the Meshy retexture.

- Planar dissolve (DISSOLVE_DEG) per part, then a collapse decimation of the parts over their budget (RATIO), so the
  flat panels lose their extra triangles first and round silhouettes keep their segments; triangulated.
- Shading: every face smooth, edges sharp where the faces meet at more than SHARP_DEG (real breaks: panel edges,
  caps, collars), so the curved housings and barrels shade smoothly (the user disliked faceting in round 1).
- UVs: xatlas charts and packing (scripts/xatlas_uv.py in work/xatlas_venv) of the joined parts into the whole square
  atlas (2048x2048 retexture, about 4 texel padding). Blender's Smart UV shattered the faceted Meshy shells into thousands
  of islands (36 % coverage at 66-80 degrees; merged islands closed whole shells and failed to unwrap).
Reads work/harvester_parts_raw.blend; writes work/harvester_uv.blend and texturing/harvester_neutral_upload.glb (only
when absent; later runs write work/harvester_neutral_rebuild.glb)."""
import json
import math
import os
import subprocess
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = 'harvester'
SHARP_DEG = 38.0
DISSOLVE_DEG = 2.0
XATLAS_PY = os.path.join(HERE, 'work', 'xatlas_venv', 'bin', 'python')
RATIO = {0: 0.72, 1: 0.9}                                # body, drill; the rest keep their triangles

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_parts_raw.blend'))
src = bpy.data.objects[NAME]
drill_axis = list(src['drill_axis'])


def split_parts(obj):
    """One object per part value (a copy each); returns {part: object}."""
    out = {}
    part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
    for p in sorted(set(part.tolist())):
        me = obj.data.copy()
        bm = bmesh.new(); bm.from_mesh(me)
        layer = bm.faces.layers.int['part']
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] != p], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(f'{NAME}_p{p}', me)
        bpy.context.scene.collection.objects.link(o)
        out[p] = o
    return out


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


parts = split_parts(src)
bpy.data.objects.remove(src)
report = {}
for p, o in parts.items():
    before = tris(o)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.scene.objects:
        x.select_set(x is o)
    m = o.modifiers.new('planar', 'DECIMATE'); m.decimate_type = 'DISSOLVE'
    m.angle_limit = math.radians(DISSOLVE_DEG); m.delimit = {'NORMAL'}
    bpy.ops.object.modifier_apply(modifier='planar')
    m = o.modifiers.new('tri', 'TRIANGULATE'); m.quad_method = 'SHORTEST_DIAGONAL'; m.min_vertices = 4
    bpy.ops.object.modifier_apply(modifier='tri')
    target = int(before * RATIO.get(p, 1.0))
    if tris(o) > target:
        m = o.modifiers.new('collapse', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
        m.ratio = target / tris(o); m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='collapse')
    report[p] = [before, tris(o)]
print('REDUCE', json.dumps(report))

for o in parts.values():
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) != 2 or e.calc_face_angle(0.0) > math.radians(SHARP_DEG))
    bm.to_mesh(o.data); bm.free()


for x in bpy.context.scene.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = obj.data.name = NAME
me = obj.data
assert all(len(p.vertices) == 3 for p in me.polygons)
pos = np.array([v.co[:] for v in me.vertices], np.float32)
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
io_in, io_out = os.path.join(HERE, 'work', 'xatlas_in.npz'), os.path.join(HERE, 'work', 'xatlas_out.npz')
np.savez(io_in, positions=pos, triangles=tri)
print(subprocess.run([XATLAS_PY, os.path.join(HERE, 'scripts', 'xatlas_uv.py'), io_in, io_out], check=True,
                     capture_output=True, text=True).stdout.strip())
uvs = np.load(io_out)['uv']
for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
uv = me.uv_layers.new(name='UVMap').data
for p in me.polygons:
    for k, li in enumerate(p.loop_indices):
        uv[li].uv = uvs[p.index, k]
obj['drill_axis'] = drill_axis
part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
counts = {int(p): int(sum(len(obj.data.polygons[i].vertices) - 2 for i in np.where(part == p)[0])) for p in set(part)}
print('PART_TRIS', json.dumps(counts), 'total', sum(counts.values()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_uv.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
for x in bpy.context.scene.objects:
    x.select_set(x is obj)
# the uploaded file (meshy job harvester_retexture_v1) is kept: xatlas packs a little differently from run to run, and
# only the retexture's own mesh matters from here on (adopt_retexture.py)
upload = os.path.join(HERE, 'texturing', f'{NAME}_neutral_upload.glb')
if os.path.exists(upload):
    upload = os.path.join(HERE, 'work', f'{NAME}_neutral_rebuild.glb')
bpy.ops.export_scene.gltf(filepath=upload, use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UV_DONE')
