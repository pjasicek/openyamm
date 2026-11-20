"""MM6 guard copy of mm9_guard_claude/scripts/rig_guard.py (mail skirt hinges at our belt, bare forearm part 17 with the arm bands).
Weight the fitted guard to the MM9 skeleton, by structure, not by distance (rules of mm9_imp_claude/scripts/rig_imp.py and the humanoid
playbook): torso bands, arm bands along the bent arm, head above a plane through the chin and nape (chin and jaw all Head), leg bands,
garment pieces rigid or copied from the skin under them. Tunic skirt: six hinge bones `Skirt_*` at the belt, children of Bip01 Spine, weighted
round the ring and by height, keyed by scripts/skirt_keys.py so the thighs stay under the cloth. Exactly symmetric by construction.
Args: <fit blend> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
FIT, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
HZ = 0.01; CY = 0.06
HINGES = {'Skirt_FR': (-0.078, -0.084, HZ), 'Skirt_FL': (0.078, -0.084, HZ), 'Skirt_SL': (0.205, 0.072, HZ), 'Skirt_BL': (0.08, 0.20, HZ), 'Skirt_BR': (-0.08, 0.20, HZ), 'Skirt_SR': (-0.205, 0.072, HZ)}
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SR']
ANG = np.array([np.arctan2(HINGES[k][1] - CY, HINGES[k][0]) for k in ['Skirt_FR', 'Skirt_FL', 'Skirt_SL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SR']])
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
sp = eb['Bip01 Spine']; Rt = sp.matrix.to_3x3()
Mi = arm.matrix_world.inverted()
for n, h in HINGES.items():
    b = eb.new(n); hp = Mi @ Vector(h)
    b.head = hp; b.tail = hp + Rt.col[1] * 0.08; b.align_roll(Rt.col[2]); b.parent = sp; b.use_connect = False; b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
for n, h in HINGES.items(): J[n] = np.array(h)
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
W = np.zeros((n, len(bones)))


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def poly_param(Q, pts):
    best = np.full(len(Q), 1e9); s = np.zeros(len(Q)); L0 = 0.0
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        ab = b - a; L = np.linalg.norm(ab)
        t = (Q - a) @ ab / (L * L)
        tc = np.clip(t, 0, 1)
        if k == 0: tc = np.minimum(t, 1)
        if k == len(pts) - 2: tc = np.maximum(tc, 0) if k else t
        d = np.linalg.norm(Q - a - np.outer(tc, ab), axis=1)
        m = d < best
        best[m] = d[m]; s[m] = L0 + tc[m] * L
        L0 += L
    return s, best


def add(ids, name, w):
    W[ids, bidx[name]] += w


def torso(ids):
    z = P[ids, 2]; ax = np.abs(P[ids, 0])
    w1 = sstep(z, 0.19, 0.29); w2 = sstep(z, 0.36, 0.46)
    add(ids, 'Bip01 Spine', 1 - w1); add(ids, 'Bip01 Spine1', w1 * (1 - w2))
    wc = w2 * sstep(ax, 0.10, 0.20) * sstep(z, 0.44, 0.50)
    add(ids, 'Bip01 Spine2', w2 - wc)
    for s, sx in (('R', -1), ('L', 1)):
        m = np.sign(P[ids, 0]) == sx
        W[ids[m], bidx[f'Bip01 {s} Clavicle']] += wc[m]


# tunic and sleeves
ids = np.nonzero(np.isin(vp, [1, 17]))[0]
torso(ids)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd, cl = [J[f'Bip01 {s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & np.isin(vp, [1, 17]))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua); L = Lu + np.linalg.norm(hd - fa)
    wa = sstep(t, -0.07, 0.07) * sstep(np.abs(P[q, 0]), 0.13, 0.235)
    we = sstep(t, Lu - 0.05, Lu + 0.05)
    W[q] *= (1 - wa)[:, None]
    add(q, f'Bip01 {s} UpperArm', wa * (1 - we)); add(q, f'Bip01 {s} Forearm', wa * we)
# gauntlets, elbow fins: rigid on the forearm
for s, sx in (('R', -1), ('L', 1)):
    q = np.nonzero(np.isin(vp, [8, 14]) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'Bip01 {s} Forearm', 1.0)
    # the hands go to the graft; until then rigid on the hand
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'Bip01 {s} Hand', 1.0)
# helmet, badge
q = np.nonzero(np.isin(vp, [3, 11]))[0]; add(q, 'Bip01 Head', 1.0)
# face and neck: head above the chin-nape plane
q = np.nonzero(vp == 2)[0]
a, b = np.array([0, -0.06, 0.672]), np.array([0, 0.15, 0.70])
tv = (b - a) / np.linalg.norm(b - a); nrm = np.cross(tv, [1, 0, 0]); nrm *= np.sign(nrm[2])
wh = sstep((P[q] - a) @ nrm, -0.018, 0.018)
add(q, 'Bip01 Head', wh)
wb = (1 - wh) * (1 - sstep(P[q, 2], 0.60, 0.66)) * 0.45
add(q, 'Bip01 Spine2', wb); add(q, 'Bip01 Neck', 1 - wh - wb)
# belt, buckle: pelvis block
q = np.nonzero(np.isin(vp, [9, 10]))[0]; add(q, 'Bip01 Spine', 1.0)
# skirt: hinges round the ring, by height
q = np.nonzero(vp == 7)[0]
ang = np.arctan2(P[q, 1] - CY, P[q, 0])
r = 1 - sstep(P[q, 2], -0.07, 0.03)
sw = np.zeros((len(q), 6))
A = np.r_[ANG, ANG[0] + 2 * np.pi]
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
for k in range(6):
    m = (aa >= A[k]) & (aa < A[k + 1])
    u = sstep((aa[m] - A[k]) / (A[k + 1] - A[k]), 0, 1)
    sw[m, k] = 1 - u; sw[m, (k + 1) % 6] = u
for k, nm in enumerate(RING):
    add(q, nm, sw[:, k] * r)
add(q, 'Bip01 Spine', 1 - r)
# legs
for s, sx in (('R', -1), ('L', 1)):
    th, ca, fo, to = [J[f'Bip01 {s} {x}'] for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
    q = np.nonzero((vp == 5) & ((np.sign(P[:, 0]) == sx) | (P[:, 0] == 0)))[0]
    t, d = poly_param(P[q], [th, ca, fo])
    Lt = np.linalg.norm(ca - th)
    wt = sstep(t, -0.07, 0.05) * sstep(np.abs(P[q, 0]), 0.0, 0.035)
    wk = sstep(t, Lt - 0.075, Lt + 0.075)
    W[q] *= 0
    add(q, f'Bip01 {s} Thigh', wt * (1 - wk)); add(q, f'Bip01 {s} Calf', wt * wk); add(q, 'Bip01 Spine', 1 - wt)
    q = np.nonzero((vp == 6) & (np.sign(P[:, 0]) == sx))[0]
    z = P[q, 2]; y = P[q, 1]
    wf = 1 - sstep(z, fo[2] - 0.035, fo[2] + 0.035)
    wy = sstep(-(y - to[1]), -0.02, 0.03) * (1 - sstep(z, to[2] + 0.03, to[2] + 0.07))
    add(q, f'Bip01 {s} Calf', 1 - wf); add(q, f'Bip01 {s} Foot', wf * (1 - wy)); add(q, f'Bip01 {s} Toe0', wf * wy)
# soften the bands inside each garment (2 passes), then pieces copied from the skin under them
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [3, 4, 8, 9, 10, 11, 14])
    new[keep] = W[keep]
    W = new
for pc in (13, 15):
    for c in np.unique(comp[vp == pc]):
        ids = np.nonzero(comp == c)[0]
        cen = P[ids].mean(0)
        host = np.nonzero(~np.isin(vp, [13, 15]))[0]
        k = host[np.argsort(np.linalg.norm(P[host] - cen, axis=1))[:6]]
        W[ids] = W[k].mean(0)
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for b in bones: body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = arm; body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
rep = dict(verts=n, tris=len(me.polygons), usage={bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0.5).any()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep)[:700])
