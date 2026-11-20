"""Weight the fitted 'Body' to the MM9 skeleton (after mm9_lobber_claude/scripts/rig_body.py).

Args: <fit blend> <config json> <out blend> <report json>

- Labels: each vertex takes the bone of the nearest MM9 vertex (the MM9 skin is rigid, one bone per vertex); a
  lateral vertex (attribute 'side' -1/1) only considers MM9 vertices whose bone is central or on its own side, so a
  leg or wing never borrows the other one's bone. Config 'groups' (optional): {name: [bones]} restricts the vertices
  nearest to any bone of a group to that group (e.g. the wing membrane only takes wing bones).
- Smooth along the mesh: weights diffuse ('diffuse' iterations) with config 'fixed' bones held (jaw hinges), then
  'hinge' free iterations.
- Small pieces (piece 2: teeth, spikes) are rigid with their nearest body vertex.
- At most four influences, normalised; weights under 0.02 dropped. The MM9 meshes are deleted; a 'bone' colour
  attribute shows the weights.
"""
import bpy, bmesh, sys, json
from mathutils.kdtree import KDTree
from mathutils import Vector
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, CFGF, OUT, REP = argv
cfg = json.load(open(CFGF))
DIFFUSE = cfg.get('diffuse', 10)
HINGE = cfg.get('hinge', 2)
FIXED = set(cfg.get('fixed', []))
SIDE_X = cfg.get('side_x', 0.04)

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
J = {b.name: b.head_local.copy() for b in arm.data.bones}
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    for v in o.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(o.vertex_groups[g.group].name)
mlab = np.array(mlab)
bside = {b: (0 if abs(p.x) < SIDE_X else (1 if p.x > 0 else -1)) for b, p in J.items()}
msd = np.array([bside[b] for b in mlab])


def tree(ids):
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


trees = {sd: tree([i for i in range(len(mpos)) if msd[i] in (0, sd)]) for sd in (-1, 1)}
trees[0] = tree(list(range(len(mpos))))
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
side = np.array([d.value for d in me.attributes['side'].data])
W = np.zeros((n, len(bones)))
first = np.empty(n, dtype=object)
for i, v in enumerate(me.vertices):
    k, ids = trees[int(side[i])]
    first[i] = mlab[ids[k.find(v.co)[1]]]
# groups: a vertex whose nearest bone is in a group takes the nearest MM9 vertex of that group (on its side)
gtrees = {}
for gname, gb in cfg.get('groups', {}).items():
    gb = set(gb)
    for sd in (-1, 0, 1):
        ids = [i for i in range(len(mpos)) if mlab[i] in gb and (sd == 0 or msd[i] in (0, sd))]
        if ids:
            gtrees[(gname, sd)] = tree(ids)
bone_group = {b: g for g, bl in cfg.get('groups', {}).items() for b in bl}
if cfg.get('surface', True):
    # nearest point on the MM9 surface (triangles whose bones are central or on the vertex's side), its barycentric
    # blend of the three corner bones (each MM9 vertex is rigid)
    from mathutils.bvhtree import BVHTree
    tris = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name == 'Body':
            continue
        vg = {g.index: g.name for g in o.vertex_groups}
        dom = [vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else None for v in o.data.vertices]
        for p in o.data.polygons:
            if len(p.vertices) == 3 and all(dom[j] for j in p.vertices):
                tris.append(([o.matrix_world @ o.data.vertices[j].co for j in p.vertices], [dom[j] for j in p.vertices]))
    bvhs = {}
    for sd in (-1, 0, 1):
        sel = [t for t in tris if sd == 0 or all(bside[b] in (0, sd) for b in t[1])]
        bvhs[sd] = (BVHTree.FromPolygons([tuple(c) for t in sel for c in t[0]],
                                          [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(sel))]), sel)
    for i, v in enumerate(me.vertices):
        bvh, sel = bvhs[int(side[i])]
        loc, nrm, fi, d = bvh.find_nearest(v.co)
        a, b_, c = sel[fi][0]
        v0, v1, v2 = b_ - a, c - a, loc - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-14:
            bc = [1 / 3] * 3
        else:
            l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den
            bc = [max(0.0, 1 - l1 - l2), max(0.0, l1), max(0.0, l2)]
        sb = sum(bc) or 1.0
        for bn, x in zip(sel[fi][1], bc):
            W[i, bidx[bn]] += x / sb
else:
    for i, v in enumerate(me.vertices):
        b = first[i]
        g = bone_group.get(b)
        if g is not None and (g, int(side[i])) in gtrees:
            k, ids = gtrees[(g, int(side[i]))]
            b = mlab[ids[k.find(v.co)[1]]]
        W[i, bidx[b]] = 1

nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
body_v = piece == 0
fixed = np.array([body_v[i] and any(W[i, bidx[b]] > 0 for b in FIXED if b in bidx) for i in range(n)])


def diffuse(W, iters, hold):
    for _ in range(iters):
        avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
        new = 0.5 * W + 0.5 * avg
        keep = hold | ~body_v
        new[keep] = W[keep]
        W = new
    return W


W = diffuse(W, DIFFUSE, fixed)
W = diffuse(W, HINGE, np.zeros(n, bool))

body_ids = np.nonzero(body_v)[0]
kb = KDTree(len(body_ids))
for j, i in enumerate(body_ids):
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
    W[comp] = W[body_ids[kb.find(me.vertices[best].co)[1]]]
    pieces += 1

order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
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
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
col = me.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(7)
pal = rng.uniform(0.15, 1.0, (len(bones), 3))
for i in range(n):
    col.data[i].color = (*(W[i, :, None] * pal).sum(0), 1.0)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
