"""Floor contacts of the rubble for the LOD build: blender -b -P rubble_contacts.py -- <lod0.glb>. For every rubble
piece, the vertex lowest in the Dead pose and the lowest over Death frames 12-18 (playbook MM8 lessons: lock Death/Dead
floor contacts in LODs; installed LOD3 went 3 mm, a first rebuild 8.5 mm under the floor). Writes the rest positions
(model space, Z up) to work/lod_protect.json under 'Rubble'."""
import json, os, sys, bpy, numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o = next(x for x in bpy.data.objects if x.type == 'MESH' and x.data.name == 'BandShard')
rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE'); sc = bpy.context.scene
me = o.data; n = len(me.vertices)
parent = list(range(n))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
for e in me.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b: parent[a] = b
# glTF splits vertices at seams: join coincident ones into one piece too
rest = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices]); key = {}
for i, p in enumerate(np.round(rest, 6).tolist()):
    j = key.setdefault(tuple(p), i)
    if find(i) != find(j): parent[find(i)] = find(j)
piece = np.array([find(i) for i in range(n)])
def posed(clip, f):
    rig.animation_data.action = bpy.data.actions[clip]
    if bpy.data.actions[clip].slots: rig.animation_data.action_slot = bpy.data.actions[clip].slots[0]
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    a = np.array([(o.matrix_world @ v.co)[:] for v in m.vertices]); e.to_mesh_clear(); return a
z = np.stack([posed('Dead', 0)[:, 2]] + [posed('Death', f)[:, 2] for f in range(12, 19)])
points = set()
for row in z:
    for pc in np.unique(piece):
        ids = np.flatnonzero(piece == pc); i = ids[row[ids].argmin()]
        if row[i] < .04:
            points.add(tuple(np.round(rest[i], 6).tolist()))
path = os.path.join(P, 'work', 'lod_protect.json'); data = json.load(open(path)) if os.path.exists(path) else {}
data['Rubble'] = sorted(points); json.dump(data, open(path, 'w'), indent=1)
print('CONTACTS', len(np.unique(piece)), 'pieces', len(points), 'points; lowest Dead %.4f' % z[0].min())
