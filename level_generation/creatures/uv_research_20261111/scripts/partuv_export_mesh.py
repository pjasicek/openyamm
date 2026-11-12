"""PartUV study (uv_research_20261111/partuv): dump one triangulated mesh in its bind pose for the PartUV / packing
scripts that run outside Blender.

Args: <in .blend|.glb> <mesh object name> <out npz> [head=Bone1,Bone2,...] [material=<substring>]
  material: only the faces whose material name contains the substring (one texture set of a multi-set body);
  the npz keeps `face_index` (indices into the full mesh) so the UVs can be written back.
npz: pos (N x 3, mesh-local bind coordinates), tri (M x 3), head (M bool, >= 0.5 weight on the head groups as in
claude_shared/uv_atlas.py), uv (M x 3 x 2, the mesh's current first UV layer), face_index (M), weights (N x G skin
weights) and groups (G vertex group names).
"""
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, NAME, OUT = argv[:3]
opts = dict(a.split('=', 1) for a in argv[3:])
if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for b in o.pose.bones:
            b.matrix_basis.identity()
bpy.context.view_layer.update()
obj = bpy.data.objects[NAME]
me = obj.data
assert all(len(p.vertices) == 3 for p in me.polygons), 'mesh must be triangulated'
pos = np.array([v.co for v in me.vertices], np.float64)
tri = np.array([p.vertices[:] for p in me.polygons], np.int64)
faces = np.arange(len(tri))
if 'material' in opts:
    keep = [i for i, m in enumerate(me.materials) if m and opts['material'] in m.name]
    mi = np.array([p.material_index for p in me.polygons])
    faces = np.nonzero(np.isin(mi, keep))[0]
    print('materials', [m.name for m in me.materials if m], 'kept', keep, len(faces))
head = np.zeros(len(tri), bool)
if opts.get('head'):
    names = opts['head'].split(',')
    groups = {obj.vertex_groups[g].index for g in names if g in obj.vertex_groups}
    weight = np.array([sum(g.weight for g in v.groups if g.group in groups) for v in me.vertices])
    head = weight[tri].mean(1) >= 0.5
uv = np.zeros((len(tri), 3, 2))
if me.uv_layers:
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get('uv', flat)
    flat = flat.reshape(-1, 2)
    uv = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
# skin weights per vertex (columns: vertex groups), for a bone-based part tree instead of PartField
weights = np.zeros((len(pos), max(len(obj.vertex_groups), 1)), np.float32)
for v in me.vertices:
    for g in v.groups:
        weights[v.index, g.group] = g.weight
groups = np.array([g.name for g in obj.vertex_groups] or ['none'])
# compact to the chosen faces' vertices
used = np.unique(tri[faces])
remap = np.full(len(pos), -1)
remap[used] = np.arange(len(used))
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
np.savez(OUT, pos=pos[used], tri=remap[tri[faces]], head=head[faces], uv=uv[faces], face_index=faces,
         vert_index=used, weights=weights[used], groups=groups)
print('EXPORTED', OUT, len(used), 'vertices', len(faces), 'triangles', int(head[faces].sum()), 'head')
