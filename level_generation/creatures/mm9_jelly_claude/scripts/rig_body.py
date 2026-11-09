"""Weight the fitted 'Body' to the MM9 skeleton (from mm9_lobber_claude/scripts/rig_body.py; body 'jelly' added).

Args: <fit blend> <body: lobber|pod> <out blend> <report json>

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
DIFFUSE = 10 if sys.argv[-3] != "jelly" else 30  # jelly: softer rib transitions on the dense bell
HINGE = 2
CHAINS = {
    'lobber': [['XApivot', 'XAarm', 'XAmid', 'XAclaw'], ['XApivot01', 'XAarm01', 'XAmid01', 'XAclaw01'],
               ['XBpiv', 'XBarm', 'XBmid', 'XBclaw'], ['XBpiv01', 'XBarm01', 'XBmid01', 'XBclaw01'],
               ['XCbase', 'XCpiv', 'XCarm'], ['XCbase01', 'XCpiv01', 'XCarm01'],
               ['Xstembase', 'XstemA', 'XstemB', 'XstemC', 'Xpodbase']],
    'jelly': [['Xarmpiv', 'XarmA', 'XarmB', 'XarmC', 'XarmD'], ['Xarmpiv01', 'XarmA01', 'XarmB01', 'XarmC01', 'XarmD01'],
              ['Xarmpiv02', 'XarmA02', 'XarmB02', 'XarmC02', 'XarmD02'],
              ['Xarmpiv03', 'XarmA03', 'XarmB03', 'XarmC03', 'XarmD03'],
              ['Xtailpiv', 'Xtail'], ['Xtail', 'XtailA', 'XtailB', 'XtailD']],
    'pod': [['Xarmpiv', 'Xarm', 'Xspike', 'Xclaw'], ['Xarmpiv01', 'Xarm02', 'Xspike01', 'Xclaw01'],
            ['Xalegpiv', 'Xaleg', 'Xarm.001', 'Xatip'], ['Xalegpiv01', 'Xaleg01', 'Xarm01', 'Xatip01'],
            ['Xblegpiv', 'Xbleg', 'Xbarm', 'Xbtip']],
}[BODY]
FIXED = {'lobber': {'Xjawpiv', 'Xjaw', 'Xmouth', 'Xchin', 'Xhead', 'Xheadmid'},
         'pod': {'Xhead', 'Xmouth', 'Xjawpiv', 'Xjaw'}, 'jelly': set()}[BODY]

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
mpos, mlab, mobj = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(o.vertex_groups[g.group].name)
        mobj.append(o.name)
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
# jelly: core vertices up in the bell (z > BELL_Z) take only the MM9 bell's own labels (not the tail top or the leg
# pivots that sit inside the bell), so the bell underside never swings with the tail or a leg.
BELL_Z = 0.25
bell_tree = tree([i for i in range(len(mpos)) if mobj[i] == 'bell.mesh' and mlab[i] != 'Xtailpiv']) \
    if BODY == 'jelly' else None

bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    k, ids = trees[chain[i]] if 0 <= chain[i] < len(CHAINS) else (
        bell_tree if bell_tree is not None and v.co.z > BELL_Z else core_tree)
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
    if BODY == 'jelly':
        # spikes hang from the stinger node (MM9: Xtail), the collar rings sit on the centre (XCENTER)
        cz = sum(me.vertices[i].co.z for i in comp) / len(comp)
        W[comp] = 0
        W[comp, bidx['Xtail' if cz < 0 else 'XCENTER']] = 1
    else:
        best = min(comp, key=lambda i: kb.find(me.vertices[i].co)[2])
        W[comp] = W[body_ids[kb.find(me.vertices[best].co)[1]]]
    pieces += 1

if BODY == 'jelly':
    # the bell is two shells (top skin, dark underside): the underside copies the weights of the top-shell vertex at
    # the same azimuth and relative radius, so the two shells fold together when MM9 collapses the bell
    bmc = bmesh.new(); bmc.from_mesh(me); bmc.verts.ensure_lookup_table()
    seen_c, shells = set(), []
    for v in bmc.verts:
        if v.index in seen_c or piece[v.index] != 0:
            continue
        comp, st = [], [v]; seen_c.add(v.index)
        while st:
            x = st.pop(); comp.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen_c:
                    seen_c.add(y.index); st.append(y)
        zs = np.array([me.vertices[i].co.z for i in comp])
        if zs.min() > BELL_Z - 0.05 and len(comp) > 300:
            shells.append((zs.mean(), comp))
    shells.sort(key=lambda t: -t[0])
    if len(shells) >= 2:
        top, under = shells[0][1], shells[1][1]
        rt = max(np.hypot(me.vertices[i].co.x, me.vertices[i].co.y) for i in top)
        ru = max(np.hypot(me.vertices[i].co.x, me.vertices[i].co.y) for i in under)
        kt = KDTree(len(top))
        for j, i in enumerate(top):
            c = me.vertices[i].co
            kt.insert((c.x / rt, c.y / rt, 0.0), j)
        kt.balance()
        for i in under:
            c = me.vertices[i].co
            W[i] = W[top[kt.find((c.x / ru, c.y / ru, 0.0))[1]]]
        shells_info = {'top': len(top), 'under': len(under)}
    else:
        shells_info = {'shells': len(shells)}
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
rep = {'bell_shells': shells_info if BODY == 'jelly' else None, 'verts': n, 'pieces_rigid': pieces, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
