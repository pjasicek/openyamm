"""Doom Bug (giant cricket) exoskeleton rig (quadruped playbook, "Spiders and other segmented creatures"): Smart
Topology returned the cricket as rigid chitin pieces. Pieces touching (closest vertices within 2 cm) form a tree rooted at
the body piece; every piece gets one bone from its junction with its parent piece toward its child junction (or its far
end) and binds 100 % to it. The legs are the subtrees that reach the floor; their first two pieces get two-bone IK in
the clips. Then collapse decimation (weights kept), triangulation, uv_atlas.unwrap (head pieces 1.5x denser) and the
static Meshy upload texturing/bug_upload.glb. Writes work/bug_rig.blend and work/bug_rig.json (tree, legs, roles).
Refuses to overwrite an existing upload."""
import bpy, os, sys, json, bmesh, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
if os.path.exists(os.path.join(HERE, 'texturing', 'bug_upload.glb')):
    raise SystemExit('texturing/bug_upload.glb exists')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'bug_clean.blend'))
m = bpy.data.objects['Bug']
d = np.load(os.path.join(HERE, 'work', 'bug_pieces.npz')); co, lab = d['co'], d['label']
# The left middle leg came back as a femur only (piece 6 ends in the air): complete it with the right middle leg's
# tibia, tarsus and claws (pieces 20, 14, 35, 38, 39) mirrored across x = 0, normals flipped.
MIRROR = [20, 14, 35, 38, 39]
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
orig_faces = [(f, [v.index for v in f.verts]) for f in bm.faces]
base_n = int(lab.max() + 1)
new_lab = list(lab)
for k, piece in enumerate(MIRROR):
    vids = set(np.where(lab == piece)[0].tolist())
    faces = [vs for f, vs in orig_faces if vs[0] in vids]
    remap = {}
    for vi in sorted(vids):
        c = co[vi]
        nv = bm.verts.new((-c[0], c[1], c[2])); remap[vi] = nv
        new_lab.append(base_n + k)
    for vs in faces:
        bm.faces.new([remap[v] for v in reversed(vs)])
bm.verts.index_update(); bm.to_mesh(m.data); bm.free()
lab = np.array(new_lab)
co = np.array([v.co[:] for v in m.data.vertices])
assert len(co) == len(lab)
MIRRORED = {piece: base_n + k for k, piece in enumerate(MIRROR)}
n = lab.max() + 1
P = [co[lab == i] for i in range(n)]


def closest(a, b):
    best = (1e9, None, None)
    for k in range(0, len(a), 400):
        A = a[k:k + 400]
        dd = ((A[:, None, :] - b[None, :, :]) ** 2).sum(-1)
        j = np.unravel_index(dd.argmin(), dd.shape)
        if dd[j] < best[0]:
            best = (float(dd[j]), A[j[0]], b[j[1]])
    return math.sqrt(best[0]), (best[1] + best[2]) / 2


dist = {}
for i in range(n):
    for j in range(i + 1, n):
        if np.linalg.norm(P[i].mean(0) - P[j].mean(0)) > 0.9 or i >= base_n or j >= base_n:
            continue
        dist[(i, j)] = dist[(j, i)] = closest(P[i], P[j])
# tree: Prim from the body piece (0) over the contact graph, preferring short gaps
parent = {0: None}; junction = {}
while len(parent) < n:
    cand = [(dist[(a, b)][0], a, b) for (a, b) in dist if a in parent and b not in parent]
    if not cand:
        break
    g, a, b = min(cand)
    parent[b] = a; junction[b] = dist[(a, b)][1]
orphans = [i for i in range(n) if i not in parent]
for i in orphans:                                   # pieces floating free: attach to the nearest piece in the tree
    g, a = min((np.linalg.norm(P[i].mean(0) - P[a].mean(0)), a) for a in parent)
    parent[i] = a; junction[i] = P[i].mean(0)
# anatomical corrections of the contact tree (read from the piece listing of `bug_rig.py tree`): the thorax shield
# carries the head, every coxa hangs on the body, the middle and hind femurs on their own coxa / the body
OVERRIDE = {2: 0, 1: 2, 24: 1, 52: 0, 33: 0, 16: 33, 37: 0, 6: 37, 47: 0, 17: 47, 4: 0,
            MIRRORED[20]: 6, MIRRORED[14]: MIRRORED[20], MIRRORED[35]: MIRRORED[14], MIRRORED[38]: MIRRORED[14],
            MIRRORED[39]: MIRRORED[14]}
for c, p in OVERRIDE.items():
    parent[c] = p
    junction[c] = closest(P[c], P[p])[1]
children = {i: [c for c, p in parent.items() if p == i] for i in range(n)}


def subtree(i):
    out = [i]
    for c in children[i]:
        out += subtree(c)
    return out


# bones
arm = bpy.data.armatures.new('Bug_Rig'); rig = bpy.data.objects.new('Bug_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
heads, tails = {}, {}
for i in range(n):
    if i == 0:
        c = P[0]
        heads[i] = np.array([0, c[:, 1].max() * 0.6, c[:, 2].mean()]); tails[i] = np.array([0, c[:, 1].min() * 0.6, c[:, 2].mean()])
        continue
    h = junction[i]
    ch = children[i]
    if ch:
        t = max((junction[c] for c in ch), key=lambda p: np.linalg.norm(p - h))
    else:
        t = P[i][np.argmax(np.linalg.norm(P[i] - h, axis=1))]
    if np.linalg.norm(t - h) < 0.01:
        t = h + np.array([0, 0, 0.02])
    heads[i], tails[i] = h, t
names = {i: f'P{i:02d}' for i in range(n)}
names[0] = 'Body'
order = sorted(parent, key=lambda i: len([1 for _ in iter(lambda: None, 0)]) if False else 0)
done = set()


def make(i):
    b = eb.new(names[i]); b.head = Vector(heads[i]); b.tail = Vector(tails[i])
    if parent[i] is not None:
        b.parent = eb[names[parent[i]]]
    done.add(i)
    for c in children[i]:
        make(c)


make(0)
bpy.ops.object.mode_set(mode='OBJECT')
# rigid weights per piece
for v in m.vertex_groups: m.vertex_groups.remove(v)
groups = {i: m.vertex_groups.new(name=names[i]) for i in range(n)}
for i in range(n):
    groups[i].add([int(x) for x in np.where(lab == i)[0]], 1.0, 'REPLACE')
m.parent = rig
mod = m.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
# legs: children of the body (or of the thorax/head pieces) whose subtree reaches the floor and lies to the side
# legs (femur, tibia, tarsus; the coxa stays on the body); the left middle leg's tibia and tarsus are the mirrored copies
LEGS = {'L1': [15, 21, 5], 'R1': [16, 22, 12], 'L2': [6, MIRRORED[20], MIRRORED[14]], 'R2': [17, 20, 14], 'L3': [3, 13, 9], 'R3': [4, 11, 10]}
legs = []
for key, chain in LEGS.items():
    foot = P[chain[-1]]
    legs.append({'key': key, 'side': key[0], 'chain': [names[k] for k in chain],
                 'foot': [float(x) for x in foot[np.argmin(foot[:, 2])]]})
heads_ = [i for i in range(n) if P[i].mean(0)[1] < -0.55 and P[i].mean(0)[2] > 0.15 and len(subtree(i)) >= 1]
info = {'tree': {names[i]: names[parent[i]] if parent[i] is not None else None for i in parent},
        'legs': legs, 'orphans': [int(x) for x in orphans], 'pieces': int(n)}
for i in sorted(parent):
    c = P[i].mean(0)
    print(f'TREE {names[i]} <- {names[parent[i]] if parent[i] is not None else None} c ({c[0]:+.2f},{c[1]:+.2f},{c[2]:.2f}) zmin {P[i][:,2].min():.2f} n {len(P[i])}')
for l in legs:
    print('LEG', l['key'], l['chain'], [round(x, 2) for x in l['foot']])
print('ORPHANS', orphans)
# head bones (for the head turn): the piece holding the eyes and its subtree = the subtree of the head piece
hp = int(np.argmax([len(p) if p.mean(0)[1] < -0.55 and abs(p.mean(0)[0]) < 0.05 else 0 for p in P]))
info['head'] = names[hp]
info['antennae'] = [names[i] for i in range(n) if (P[i].max(0) - P[i].min(0)).max() > 0.3 and P[i].mean(0)[2] > 0.5]
print('HEAD', info['head'], 'ANTENNAE', info['antennae'])
json.dump(info, open(os.path.join(HERE, 'work', 'bug_rig.json'), 'w'), indent=1)
if 'tree' in sys.argv:                               # dry run: the tree only
    raise SystemExit(0)
# reduction (weights follow), triangulate, unwrap
bpy.context.view_layer.objects.active = m
for o in bpy.data.objects: o.select_set(o == m)
t0 = len(m.data.polygons)
dec = m.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'COLLAPSE'; dec.ratio = 0.55
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_move_to_index(modifier='dec', index=0); bpy.ops.object.modifier_apply(modifier='dec')
tri = m.modifiers.new('tri', 'TRIANGULATE')
bpy.ops.object.modifier_move_to_index(modifier='tri', index=0); bpy.ops.object.modifier_apply(modifier='tri')
print('REDUCED', t0, '->', len(m.data.polygons))
head_group = [names[k] for k in subtree(hp)]
report = uv_atlas.unwrap(m, head_groups=tuple(head_group), head_factor=1.5, cut_closed=True)
print('UV', report.get('use'), report.get('charts_used'), report.get('packer_used'), report.get('fallbacks'))
info['uv'] = {k: report.get(k) for k in ('use', 'charts_used', 'packer_used', 'fallbacks')}
json.dump(info, open(os.path.join(HERE, 'work', 'bug_rig.json'), 'w'), indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'bug_rig.blend'))
up = m.copy(); up.data = m.data.copy(); up.name = 'BugUpload'; bpy.context.scene.collection.objects.link(up)
up.modifiers.clear(); up.parent = None; up.matrix_world = m.matrix_world.copy()
for o in bpy.data.objects: o.select_set(o == up)
bpy.context.view_layer.objects.active = up
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'bug_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UPLOAD bug', len(up.data.polygons))
