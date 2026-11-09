"""Weight the fitted 'Body' to the MM9 skeleton (from ../mm9_lobber_claude/scripts/rig_body.py; terror config added).

Args: <fit blend> <body: lobber|pod|terror> <out blend> <report json>

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
FIT, BODY, OUT, REP = argv
DIFFUSE = 10
HINGE = 2
CHAINS = {
    'lobber': [['XApivot', 'XAarm', 'XAmid', 'XAclaw'], ['XApivot01', 'XAarm01', 'XAmid01', 'XAclaw01'],
               ['XBpiv', 'XBarm', 'XBmid', 'XBclaw'], ['XBpiv01', 'XBarm01', 'XBmid01', 'XBclaw01'],
               ['XCbase', 'XCpiv', 'XCarm'], ['XCbase01', 'XCpiv01', 'XCarm01'],
               ['Xstembase', 'XstemA', 'XstemB', 'XstemC', 'Xpodbase']],
    'pod': [['Xarmpiv', 'Xarm', 'Xspike', 'Xclaw'], ['Xarmpiv01', 'Xarm02', 'Xspike01', 'Xclaw01'],
            ['Xalegpiv', 'Xaleg', 'Xarm.001', 'Xatip'], ['Xalegpiv01', 'Xaleg01', 'Xarm01', 'Xatip01'],
            ['Xblegpiv', 'Xbleg', 'Xbarm', 'Xbtip']],
    # Terror: the fit's chain order (fit_terror.py): six tentacles, then the right and left legs
    'terror': [['Bone26', 'Bone27', 'Bone28', 'Bone29', 'Bone30', 'Bone31', 'Bone32', 'Bone33'],
               ['Bone01', 'Bone02', 'Bone03', 'Bone04', 'Bone21', 'Bone22', 'Bone23', 'Bone24'],
               ['Bone14', 'Bone15', 'Bone16'], ['Bone05', 'Bone06', 'Bone07'],
               ['Bone13', 'Bone18', 'Bone19'], ['Bone09', 'Bone10', 'Bone11'],
               ['Bip01 R Thigh', 'Bip01 R Calf', 'Bip01 R Foot', 'Bip01 R Toe0'],
               ['Bip01 L Thigh', 'Bip01 L Calf', 'Bip01 L Foot', 'Bip01 L Toe0']],
}[BODY]
FIXED = {'lobber': {'Xjawpiv', 'Xjaw', 'Xmouth', 'Xchin', 'Xhead', 'Xheadmid'},
         'pod': {'Xhead', 'Xmouth', 'Xjawpiv', 'Xjaw'},
         'terror': {'Bone35', 'Bone36', 'Bone37', 'Bone38', 'Bone39', 'Bone40', 'Bone41'}}[BODY]

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(o.vertex_groups[g.group].name)
mlab = np.array(mlab)
chain_bones = set(b for c in CHAINS for b in c[1:])


def tree(ids):
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


trees = [tree([i for i in range(len(mpos)) if mlab[i] in c]) for c in CHAINS]
core_tree = tree([i for i in range(len(mpos)) if mlab[i] not in chain_bones])

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
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
