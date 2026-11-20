"""PartUV study: an installed creature GLB -> one welded mesh object per texture set (LOD0 only, rig kept) in a blend,
for unwrapping each set on its own square atlas.

Args: <installed glb> <LOD0 object name> <out blend> <set> [<set> ...]
  set = <name>:mat=<substring>[,<substring>...]      faces whose material name contains a substring
      | <name>:box=<u0>,<u1>,<v0>,<v1>                faces whose UV centre lies in the box (a set sharing one image)
      | <name>:mat=...&box=...                         both
The set's current UVs are mapped from the box (or kept for mat=) into 0..1 so that the current layout of the set can
be measured on its own. Vertices are welded by position (1e-6): the glTF importer splits them at every UV seam and
both unwrappers must see the connected surface. Set objects are named Set_<name>, triangulated, and keep the vertex
groups and the armature modifier.
"""
import sys

import bmesh
import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, NAME, OUT = argv[:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for b in o.pose.bones:
            b.matrix_basis.identity()
src = bpy.data.objects[NAME]
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != src:
        bpy.data.objects.remove(o)
bpy.context.view_layer.update()
for spec in argv[3:]:
    name, rule = spec.split(':', 1)
    obj = src.copy()
    obj.data = src.data.copy()
    obj.name = obj.data.name = f'Set_{name}'
    bpy.context.scene.collection.objects.link(obj)
    me = obj.data
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get('uv', flat)
    flat = flat.reshape(-1, 2)
    centre = np.array([flat[list(p.loop_indices)].mean(0) for p in me.polygons])
    keep = np.ones(len(me.polygons), bool)
    for part in rule.split('&'):
        kind, value = part.split('=', 1)
        if kind == 'mat':
            subs = value.split(',')
            keep_mats = {i for i, m in enumerate(me.materials) if m and any(s in m.name for s in subs)}
            keep &= np.array([p.material_index in keep_mats for p in me.polygons])
        else:
            u0, u1, v0, v1 = map(float, value.split(','))
            keep &= (centre[:, 0] >= u0) & (centre[:, 0] < u1) & (centre[:, 1] >= v0) & (centre[:, 1] < v1)
            flat[:, 0] = (flat[:, 0] - u0) / (u1 - u0)
            flat[:, 1] = (flat[:, 1] - v0) / (v1 - v0)
            me.uv_layers[0].data.foreach_set('uv', flat.ravel())
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep[f.index]], context='FACES')
    before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    print('SET', name, len(bm.faces), 'triangles', before, '->', len(bm.verts), 'vertices after weld')
    bm.to_mesh(me)
    bm.free()
bpy.data.objects.remove(src)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SAVED', OUT)
