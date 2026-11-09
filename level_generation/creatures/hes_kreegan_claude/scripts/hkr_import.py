"""hkr step 1: the MM6 Demon (source/mm6_demon_source.glb, installed mm6_demon.glb copied 2026-10-22) as the shared
Kreegan body. Keeps the LOD0 mesh 'Demon_Native_Mesh' (materials, UVs, normals and mixamorig weights unchanged) as
'Body'; drops the LOD/shadow meshes, the ash-remains plume and the burn extras. Adds point attributes 'piece'
(connected component after welding glTF's UV-seam splits by position), 'garment' (creature.json labels) and 'orig_co'.
Writes work/step1.blend (Body + the demon's armature 'Demon', no clips), work/demon_clips.blend (the demon's clips as Demon_src_*) and work/demon_joints.json (bone heads,
tails and rest matrices of the demon rig). Args: none"""
import bpy, os, sys, json
import numpy as np
import bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'source', 'mm6_demon_source.glb'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects['Demon_Native_Mesh']
for o in list(bpy.data.objects):
    if o not in (arm, body):
        bpy.data.objects.remove(o, do_unlink=True)
arm.name = 'Demon'
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
# weld by position for connectivity only (the mesh itself keeps its splits)
key = np.round(co / 1e-5).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
parent = np.arange(inv.max() + 1)
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for e in me.edges:
    a, b = find(inv[e.vertices[0]]), find(inv[e.vertices[1]])
    if a != b: parent[a] = b
roots = np.array([find(inv[i]) for i in range(len(co))])
ur, piece = np.unique(roots, return_inverse=True)
sizes = np.bincount(piece)
order = np.argsort(-sizes); remap = np.empty_like(order); remap[order] = np.arange(len(order))
piece = remap[piece]
me.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', piece.astype(np.int32))
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
mat_of_v = np.zeros(len(co), np.int32)
for p in me.polygons:
    for v in p.vertices: mat_of_v[v] = p.material_index
W = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda g: g.weight); W[v.index] = body.vertex_groups[g.group].name
print('PIECES', len(sizes))
for k in range(len(sizes)):
    m = piece == k; c = co[m]
    bones = {}
    for i in np.nonzero(m)[0]:
        bones[W.get(i)] = bones.get(W.get(i), 0) + 1
    top = sorted(bones.items(), key=lambda x: -x[1])[:2]
    print('PIECE', k, int(m.sum()), 'mat', sorted(set(mat_of_v[m].tolist())), 'min', np.round(c.min(0), 3).tolist(), 'max', np.round(c.max(0), 3).tolist(), top)
J = {}
for b in arm.data.bones:
    J[b.name] = {'head': list(arm.matrix_world @ b.head_local), 'tail': list(arm.matrix_world @ b.tail_local),
                 'matrix': [list(r) for r in (arm.matrix_world @ b.matrix_local)], 'parent': b.parent.name if b.parent else None}
json.dump(J, open(os.path.join(HERE, 'work', 'demon_joints.json'), 'w'), indent=1)
print('ARMWORLD', [list(r) for r in arm.matrix_world])
# the demon's own clips go to their own file (their names collide with ours); step1 keeps the body only
for a_ in list(bpy.data.actions):                   # a list: renaming re-sorts the collection
    a_.name = 'Demon_src_' + a_.name; a_.use_fake_user = True
body.hide_viewport = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'demon_clips.blend'), copy=True)
for a_ in list(bpy.data.actions):
    bpy.data.actions.remove(a_)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
