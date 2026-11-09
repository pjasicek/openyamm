"""Weight the fitted cat 'Body' to the MM9 CAT.abc skeleton (from mm9_wolf_claude/scripts/rig_body.py).

Args: <fit blend> <out blend> <report json>

- Labels: each vertex takes the bone of the nearest MM9 vertex (the MM9 skin is rigid, one bone per vertex). A limb
  vertex ('chain' attribute k) only considers the MM9 vertices of its own chain's bones; a core vertex only those
  outside the chains (their root pivots allowed), so limbs never borrow a neighbour's bone.
- Smooth along the mesh: weights diffuse (DIFFUSE iterations) with the jaw-hinge labels held, then a short free pass.
- Small pieces (piece 2: mouth tendrils, teeth) are rigid with their nearest body vertex.
- At most four influences, normalised. The MM9 meshes are deleted; a 'bone' colour attribute shows the weights.
"""
import bpy, bmesh, sys, json
from mathutils.kdtree import KDTree
from mathutils import Matrix, Vector
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
import os
DIFFUSE = int(os.environ.get('RIG_DIFFUSE', '10'))   # iterations scale with mesh density (dense voxel body: 120)
HINGE = int(os.environ.get('RIG_HINGE', '2'))
# same order as fit_quad.py CHAINS (the fit's 'chain' attribute indexes this list)
CHAINS = [['Xflegpiv01', 'Xfankle01', 'Xffoot01'], ['Xflegpiv', 'Xfankle', 'Xffoot'],
          ['Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01'],
          ['Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'],
          ['Xtailpiv', 'XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailE', 'XtailF']]
UPPER, LOWER = None, None   # the MM9 cat has no jaw bone: its mouth never opens
FIXED = set()   # upper muzzle / lower jaw: held while diffusing so the lips do not blur across the mouth

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
# the armature may carry fit_quad.py's reference pose (AIM_LEGS): labels come from the MM9 mesh in that pose, and
# the weighted Body is unposed to the bind at the end
POSED = any(pb.matrix_basis != Matrix.Identity(4) for pb in arm.pose.bones)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    me_e = o.evaluated_get(dg).to_mesh()
    for v, ve in zip(o.data.vertices, me_e.vertices):
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ ve.co)
        mlab.append(o.vertex_groups[g.group].name)
    o.evaluated_get(dg).to_mesh_clear()
mlab = np.array(mlab)
chain_bones = set(b for c in CHAINS for b in c[1:])  # root pivots stay available to the core


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


EA = np.array([tuple(e.vertices) for e in me.edges])
DEG = np.bincount(EA.ravel(), minlength=n).astype(float)


def diffuse(W, iters, hold):
    for _ in range(iters):
        acc = np.zeros_like(W)
        np.add.at(acc, EA[:, 0], W[EA[:, 1]]); np.add.at(acc, EA[:, 1], W[EA[:, 0]])
        avg = np.where(DEG[:, None] > 0, acc / np.maximum(DEG, 1)[:, None], W)
        new = 0.5 * W + 0.5 * avg
        keep = hold | ~body_v
        new[keep] = W[keep]
        W = new
    return W


# the ears: MM9 flicks them through 50 degrees and its ear bones also own skull vertices in the low-poly skin; only what
# stands off the skull (the ear flap) may follow them, the skull and the ear base stay on the head
EARS = (('Xearpiv', 'Xear'), ('Xearpiv01', 'Xear01'))
EAR_Z = float(os.environ.get('EAR_Z', '0.286'))   # ear flap above this height
hb = bidx['Xhead']
for a_, b_ in EARS:
    tip = np.array(arm.pose.bones[b_].head)
    base = np.array(arm.pose.bones[a_].head)
    keep = np.zeros(n, bool)
    co_ = np.array([tuple(v.co) for v in me.vertices])
    ear_side = co_[:, 0] * np.sign(tip[0]) > 0
    keep = ear_side & (co_[:, 2] > EAR_Z) & (np.abs(co_[:, 0]) > 0.014) & (co_[:, 1] < -0.1)
    for bn in (a_, b_):
        j = bidx[bn]
        move = (W[:, j] > 0) & ~keep
        W[move, hb] += W[move, j]
        W[move, j] = 0
    W[keep, :] = 0
    W[keep, bidx[a_]] = 1
    top = keep & (co_[:, 2] > EAR_Z + 0.01)
    W[top, bidx[a_]] = 0
    W[top, bidx[b_]] = 1
# the tail's region reaches onto the rump: only the tail tube itself follows the tail bones
TAIL = ['Xtailpiv', 'XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailE', 'XtailF']
co0 = np.array([tuple(v.co) for v in me.vertices])
ids = np.nonzero(chain == 4)[0]
hd_ = [np.array(arm.pose.bones[b].head) for b in TAIL]
hd_.append(hd_[-1] + (hd_[-1] - hd_[-2]) * 3.0)
dmin = np.full(len(ids), 1e9); lab_ = np.zeros(len(ids), int)
for k_ in range(len(TAIL)):
    a_, b_ = hd_[k_], hd_[k_ + 1]
    ab = b_ - a_
    u = np.clip(((co0[ids] - a_) @ ab) / (ab @ ab), 0, 1)
    dd = np.linalg.norm(co0[ids] - (a_ + u[:, None] * ab), axis=1)
    m_ = dd < dmin
    dmin[m_] = dd[m_]; lab_[m_] = k_
rump = (dmin > float(os.environ.get('TAIL_R', '0.018'))) & (co0[ids, 1] < 0.18)
W[ids] = 0
W[ids, [bidx[TAIL[k_]] for k_ in lab_]] = 1
core_lab = np.array([mlab[core_tree[1][core_tree[0].find(me.vertices[int(i)].co)[1]]] for i in ids[rump]])
W[ids[rump]] = 0
for i, l_ in zip(ids[rump], core_lab):
    W[i, bidx[l_]] = 1
chain[ids[rump]] = -1
# the hind legs (cat): labels by the nearest bone segment; the rest joints sit in the mesh (fit_quad.py HIND_JOINTS)
SEGS = [(2, ['Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01']), (3, ['Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'])]
co_ = np.array([tuple(v.co) for v in me.vertices])
for ch_, seq in SEGS:
    ids = np.nonzero(chain == ch_)[0]
    hd = [np.array(arm.pose.bones[b].head) for b in seq]
    hd.append(hd[-1] + (hd[-1] - hd[-2]) * 2.0)
    best = np.full(len(ids), 1e9); lab_ = np.zeros(len(ids), int)
    for k_, name in enumerate(seq):
        a_, b_ = hd[k_], hd[k_ + 1]
        ab = b_ - a_
        u = np.clip(((co_[ids] - a_) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        dd = np.linalg.norm(co_[ids] - (a_ + u[:, None] * ab), axis=1)
        m_ = dd < best
        best[m_] = dd[m_]; lab_[m_] = k_
    W[ids] = 0
    W[ids, [bidx[seq[k_]] for k_ in lab_]] = 1
W = diffuse(W, DIFFUSE, fixed)
W = diffuse(W, HINGE, np.zeros(n, bool))

# small pieces: rigid with their nearest body vertex
body_ids = np.nonzero(body_v)[0]
kb = KDTree(len(body_ids))
for j, i in enumerate(body_ids):
    kb.insert(me.vertices[i].co, j)
kb.balance()
# MM9 mouth plane: least-squares linear separation of the MM9 upper-muzzle (+1) and lower-jaw (-1) vertices
mouth_ids = [i for i in range(len(mpos)) if mlab[i] in (UPPER, LOWER)]
Xm = np.array([tuple(mpos[i]) + (1.0,) for i in mouth_ids]).reshape(-1, 4)
ym = np.array([1.0 if mlab[i] == UPPER else -1.0 for i in mouth_ids])
MOUTH_PLANE = np.linalg.lstsq(Xm, ym, rcond=None)[0] if mouth_ids else None
teeth = []
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
    cen = np.mean([tuple(me.vertices[i].co) for i in comp], 0)
    if UPPER and W[comp[0], bidx[UPPER]] + W[comp[0], bidx[LOWER]] > 0.5:
        # a tooth: the upper or lower jaw by the MM9 mouth plane
        side = UPPER if np.append(cen, 1) @ MOUTH_PLANE > 0 else LOWER
        W[comp] = 0
        W[comp, bidx[side]] = 1
        teeth.append({'n': len(comp), 'c': np.round(cen, 3).tolist(), 'bone': side})
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
unpose = {}
if POSED and os.environ.get('REST_FROM_POSE') == '1':
    # the reference pose becomes the rest pose (the cat: a standing pose instead of MM9's bind with the hind legs under
    # the belly); every bone's old basis is kept as 'rest_offset' so clips_mm9.py converts the MM9 keys
    # (new basis = offset^-1 @ old basis: the same world motion)
    # rotation only: a pose translation moved the rest joint itself, the clips keep their own offsets
    off = {pb.name: [list(r) for r in pb.matrix_basis.to_3x3().to_4x4()] for pb in arm.pose.bones
           if pb.matrix_basis != Matrix.Identity(4)}
    for o in bpy.data.objects:
        o.select_set(o == arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    arm['rest_offset_json'] = json.dumps(off)
    unpose = {'rest_from_pose': len(off)}
elif POSED:
    # inverse linear blend skinning: v_bind = (sum_b w_b S_b)^-1 v_pose, S_b = pose_b @ rest_b^-1 (armature space)
    S = np.array([np.array(arm.pose.bones[b].matrix @ arm.data.bones[b].matrix_local.inverted()) for b in bones])
    A_inv = np.array(arm.matrix_world.inverted())
    A_w = np.array(arm.matrix_world)
    mw = np.array(body.matrix_world)
    mwi = np.linalg.inv(mw)
    P = np.array([tuple(v.co) + (1.0,) for v in me.vertices]) @ mw.T @ A_inv.T
    M = np.einsum('vb,bij->vij', W, S)
    Pb = np.linalg.solve(M, P[:, :, None])[:, :, 0]
    Pw = Pb @ A_w.T @ mwi.T
    mv = np.linalg.norm(Pw[:, :3] - np.array([tuple(v.co) for v in me.vertices]), axis=1)
    for i, v in enumerate(me.vertices):
        v.co = Vector(tuple(Pw[i, :3]))
    me.update()
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    unpose = {'moved_max': round(float(mv.max()), 4), 'moved_mean': round(float(mv.mean()), 4),
              'cond_max': round(float(np.linalg.cond(M[:, :3, :3]).max()), 2)}
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
rep = {'unpose': unpose, 'verts': n, 'pieces_rigid': pieces, 'teeth': teeth, 'mouth_plane_accuracy': float(((Xm @ MOUTH_PLANE > 0) == (ym > 0)).mean()) if UPPER else None, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
