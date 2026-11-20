"""Weight the fitted Icky 'Body' to the MM9 skeleton (from mm9_lobber_claude/scripts/rig_body.py).

Args: <fit blend (with Wings)> <out blend> <report json>
Chains (the 'chain' attribute from fit_icky.py): 0 tail, 1 right leg, 2 left leg. The core lookup uses the MM9 body,
spike and tooth meshes only (the MM9 wing and foot meshes would hand the flank and belly wing/leg bones).
The 'Wings' object (build_wings.py) keeps its own weights.

- Labels: each vertex takes the bone of the nearest MM9 vertex (the MM9 skin is rigid, one bone per vertex). A limb
  vertex ('chain' attribute k) only considers the MM9 vertices of its own chain's bones; a core vertex only those
  outside the chains (their root pivots allowed), so limbs never borrow a neighbour's bone.
- Smooth along the mesh: weights diffuse (DIFFUSE iterations) with the jaw-hinge labels held, then a short free pass.
- Small pieces (piece 2: mouth tendrils, teeth) are rigid with their nearest body vertex.
- At most four influences, normalised. The MM9 meshes are deleted; a 'bone' colour attribute shows the weights.
"""
import bpy, bmesh, sys, json
from mathutils.kdtree import KDTree
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
DIFFUSE = 10
HINGE = 2
TOES = ['Xleg', 'Xfoot', 'XtoepivA', 'XtoeA', 'XtoepivC', 'XtoeC', 'XtoeB']
CHAINS = [['Xtailbase', 'XtailA', 'XtailB', 'XtailC', 'XtailD'],
          ['Xlegpiv'] + TOES, ['Xlegpiv01'] + [t + '01' for t in TOES]]
FIXED = {'Xjawpiv', 'Xjaw', 'Xjawpiv01', 'Xjaw01', 'Xjawpiv02', 'Xjaw02', 'Xjawpiv03', 'Xjaw03', 'Xjawpiv04',
         'Xjaw04', 'Xjawpiv05', 'Xjaw05', 'Xearpiv', 'Xearpiv01'}
CORE_SRC = ('body', 'spike', 'tailspike', 'tooth')
LEG_SRC = ('foot',)

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
mpos, mlab, msrc = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in ('Body', 'Wings'):
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(o.vertex_groups[g.group].name)
        msrc.append(o.name.split('.')[0].rstrip('0123456789'))
mlab = np.array(mlab)
msrc = np.array(msrc)
chain_bones = set(b for c in CHAINS for b in c[1:])


def tree(ids):
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


core_ok = np.isin(msrc, CORE_SRC)
trees = [tree([i for i in range(len(mpos)) if mlab[i] in c and (core_ok[i] or msrc[i] in LEG_SRC)]) for c in CHAINS]
core_tree = tree([i for i in range(len(mpos)) if mlab[i] not in chain_bones and core_ok[i]])

bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    k, ids = trees[chain[i]] if 0 <= chain[i] < len(CHAINS) else core_tree
    W[i, bidx[mlab[ids[k.find(v.co)[1]]]]] = 1

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

# small pieces: rigid with their nearest body vertex
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
    if o.type == 'MESH' and o.name not in ('Body', 'Wings'):
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
