"""Weight the fitted dragon 'Body' (bind pose) to the MM9 skeleton (after mm9_dfly/mm9_lobber rig_body.py).

Args: <fit blend> <out blend> <report json>

- Groups: every MM9 bone belongs to one group (two forelegs, two hind legs, two wings, tail, core = trunk, neck,
  head). A Body vertex's group comes from its Meshy-space label (fit_dragon.py 'label_meshy'), so a forearm lying
  against the chest keeps its arm. Its bone label is the nearest MM9 bind vertex of the same group.
- Wings: membrane vertices take the barycentric blend of the MM9 wing triangle under them (nearest point on the
  MM9 wing surface of that side), which reproduces MM9's own membrane stretch between the finger bones.
- Smoothing: DIFFUSE iterations along the mesh, wing and jaw/skull labels held, then HINGE free iterations.
- Small pieces (teeth, claws, horns cut loose by Meshy) are rigid with their nearest main-surface vertex.
- At most four influences, normalised. The MM9 meshes stay in the blend (hidden) for overlays.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
DIFFUSE = 12
HINGE = 3
ROOTS = {'arm_l': 'Xarmpiv02', 'arm_r': 'Xarmpiv03', 'leg_l': 'Xlegpiv02', 'leg_r': 'Xlegpiv03',
         'wing_l': 'Ywingbase', 'wing_r': 'Ywingbase01', 'tail': 'Xtail'}
HELD = {'Xjaw', 'Xjawpivot', 'Xtong', 'Xtongpiv', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01'}

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
group_of = {}
for gname, root in ROOTS.items():
    st = [arm.data.bones[root]]
    while st:
        b = st.pop(); group_of[b.name] = gname; st += list(b.children)
for b in bones:
    group_of.setdefault(b, 'core')
GROUPS = ['core'] + list(ROOTS)
gid = {g: i for i, g in enumerate(GROUPS)}

mpos, mlab = [], []
wing_tris = {'wing_l': [], 'wing_r': []}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in ('Body', 'MeshyPosed') or o.name.startswith('MM9Posed_'):
        continue
    vl = []
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        vl.append(o.vertex_groups[g.group].name)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(vl[-1])
    for p in o.data.polygons:
        gs = {group_of[vl[i]] for i in p.vertices}
        for wg in ('wing_l', 'wing_r'):
            if gs == {wg}:
                vs = [o.matrix_world @ o.data.vertices[i].co for i in p.vertices]
                for k in range(1, len(vs) - 1):
                    ids = (p.vertices[0], p.vertices[k], p.vertices[k + 1])
                    wing_tris[wg].append(([vs[0], vs[k], vs[k + 1]], [bidx[vl[i]] for i in ids]))
mlab = np.array([bidx[l] for l in mlab])
mgrp = np.array([gid[group_of[bones[l]]] for l in mlab])


def tree(ids):
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


trees = [tree([i for i in range(len(mpos)) if mgrp[i] == g]) for g in range(len(GROUPS))]
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
lm = np.array([d.value for d in me.attributes['label_meshy'].data])
vgrp = np.array([gid[group_of[bones[l]]] for l in lm])
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    k, ids = trees[vgrp[i]]
    W[i, mlab[ids[k.find(v.co)[1]]]] = 1

held = np.zeros(n, bool)
wing_stats = {}
for wg, tris in wing_tris.items():
    if not tris:
        continue
    verts, polys = [], []
    for t, _ in tris:
        polys.append([len(verts), len(verts) + 1, len(verts) + 2]); verts += t
    bvh = BVHTree.FromPolygons(verts, polys)
    sel = np.nonzero(vgrp == gid[wg])[0]
    far = 0
    for i in sel:
        co = me.vertices[i].co
        loc, nrm, ti, dist = bvh.find_nearest(co)
        if ti is None:
            continue
        (a, b, c), labs = tris[ti]
        # barycentric coordinates of loc in (a, b, c)
        bc = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        w = np.clip(np.array(bc), 0, None)
        if w.sum() <= 0:
            continue
        w /= w.sum()
        row = np.zeros(len(bones))
        for wi, li in zip(w, labs):
            row[li] += wi
        # membrane only: vertices near the wing surface; the thick arm keeps its nearest label
        if dist < 0.6:
            W[i] = row
            held[i] = True
        else:
            far += 1
    wing_stats[wg] = {'vertices': int(len(sel)), 'barycentric': int(held[sel].sum()), 'far': far}

nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
main = piece == 0
held |= main & np.array([any(W[i, bidx[b]] > 0.5 for b in HELD if b in bidx) for i in range(n)])


def diffuse(W, iters, hold):
    for _ in range(iters):
        avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
        new = 0.5 * W + 0.5 * avg
        keep = hold | ~main
        new[keep] = W[keep]
        W = new
    return W


W = diffuse(W, DIFFUSE, held)
W = diffuse(W, HINGE, np.zeros(n, bool))

main_ids = np.nonzero(main)[0]
kb = KDTree(len(main_ids))
for j, i in enumerate(main_ids):
    kb.insert(me.vertices[i].co, j)
kb.balance()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); pieces = 0
for v in bm.verts:
    if piece[v.index] != 2 or v.index in seen:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    best = min(comp, key=lambda i: kb.find(me.vertices[i].co)[2])
    W[comp] = W[main_ids[kb.find(me.vertices[best].co)[1]]]
    pieces += 1

order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
for m in list(body.modifiers):
    body.modifiers.remove(m)
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
a = me.attributes.get('chain') or me.attributes.new('chain', 'INT', 'POINT')
for i, d in enumerate(a.data):
    d.value = int(vgrp[i])
col = me.color_attributes.get('bone') or me.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(7)
pal = rng.uniform(0.15, 1.0, (len(bones), 3))
for i in range(n):
    col.data[i].color = (*(W[i, :, None] * pal).sum(0), 1.0)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name not in ('Body',):
        o.hide_render = True
        o.hide_set(True)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'groups': {g: int((vgrp == i).sum()) for i, g in enumerate(GROUPS)},
       'wings': wing_stats, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps({k: v for k, v in rep.items() if k != 'dominant_counts'}))
