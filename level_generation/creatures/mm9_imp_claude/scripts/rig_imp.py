"""Weight the fitted Imp body to the MM9 skeleton. Args: <fit blend> <config json> <out blend> <report json>

Base: each vertex takes the barycentric bone blend of the nearest MM9 surface point (own side), diffused along the mesh.
Then, by structure, not by distance: arm bands (clavicle > upper arm > forearm > hand along the bent arm), fingers from
the digits found by connectivity (fit_imp.py), tail along its chain, head above a plane through the bottom of the chin
and the nape (chin and jaw are all Head; Winged Mutant lesson), flap on Xpiv, belt rigid on the pelvis, loose pieces rigid
(teeth, eyes: Head; bracers: the bone under them). Belt, flap and bracer studs are deleted (paint, not triangles; they
would be 1.5k triangles and 35 loose pieces)."""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FIT, CFGF, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFGF))
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
SIDE_X = 0.03
bside = {b: (0 if abs(p[0]) < SIDE_X else int(np.sign(p[0]))) for b, p in J.items()}
tris = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body' or 'trident' in o.name:
        continue
    vg = {g.index: g.name for g in o.vertex_groups}
    dom = [vg[max(v.groups, key=lambda g: g.weight).group] for v in o.data.vertices]
    for p in o.data.polygons:
        tris.append(([o.matrix_world @ o.data.vertices[j].co for j in p.vertices], [dom[j] for j in p.vertices]))
bvhs = {}
for sd in (-1, 0, 1):
    sel = [t for t in tris if sd == 0 or all(bside[b] in (0, sd) for b in t[1])]
    bvhs[sd] = (BVHTree.FromPolygons([tuple(c) for t in sel for c in t[0]], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(sel))]), sel)
W = np.zeros((n, len(bones)))
sidev = np.where(np.abs(P[:, 0]) < SIDE_X, 0, np.sign(P[:, 0])).astype(int)
for i, v in enumerate(me.vertices):
    bvh, sel = bvhs[sidev[i]]
    loc, nrm, fi, d = bvh.find_nearest(v.co)
    a, b_, c = sel[fi][0]
    v0, v1, v2 = b_ - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    bc = [1 / 3] * 3 if abs(den) < 1e-14 else None
    if bc is None:
        l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den
        bc = [max(0.0, 1 - l1 - l2), max(0.0, l1), max(0.0, l2)]
    sb = sum(bc) or 1.0
    for bn, x in zip(sel[fi][1], bc):
        W[i, bidx[bn]] += x / sb
# components
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0:
        continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0:
                comp[y] = c_; st.append(y)
    c_ += 1
sizes = np.bincount(comp)
main = sizes.argmax()
body_v = comp == main
for _ in range(cfg.get('diffuse', 8)):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W = 0.5 * W + 0.5 * avg


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def poly_param(Q, pts):
    """distance along the polyline of each point's nearest position, and the distance to it"""
    best = np.full(len(Q), 1e9); s = np.zeros(len(Q)); L0 = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a; L = np.linalg.norm(ab)
        t = (Q - a) @ ab / (L * L)
        tc = np.clip(t, 0, 1)
        if a is pts[0]:
            tc = np.minimum(t, 1)        # before the first joint
        if b is pts[-1]:
            tc = np.maximum(tc, 0) if a is not pts[0] else t
        d = np.linalg.norm(Q - a - np.outer(tc, ab), axis=1)
        m = d < best
        best[m] = d[m]; s[m] = L0 + tc[m] * L
        L0 += L
    return s, best


def setw(ids, names, weights):
    """ids: vertices; weights: len(ids) x len(names); replaces all bones, scaled to the share of `share`."""
    W[ids] = 0
    for k, nm in enumerate(names):
        W[ids, bidx[nm]] = weights[:, k]


rep = {}
# arm bands
for S in ('L', 'R'):
    cl, ua, fa, hd = [f'Bip01 {S} {x}' for x in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')]
    pts = [J[ua], J[fa], J[hd]]
    fam = [cl, ua, fa, hd] + [b for b in bones if f' {S} Finger' in b]
    share = W[:, [bidx[b] for b in fam]].sum(1)
    sx = np.sign(J[ua][0])
    ids = np.nonzero(body_v & (share > 0.5) & (np.sign(P[:, 0]) == sx))[0]
    s, d = poly_param(P[ids], pts)
    Lu = np.linalg.norm(pts[1] - pts[0]); L = Lu + np.linalg.norm(pts[2] - pts[1])
    b = cfg['arm_bands']
    wu = sstep(s, b['shoulder'][0], b['shoulder'][1]); wf = sstep(s, Lu - b['elbow'], Lu + b['elbow'])
    wh = sstep(s, L + b['wrist'][0], L + b['wrist'][1])
    new = np.stack([1 - wu, wu * (1 - wf), wf * (1 - wh), wh], 1)
    # the clavicle share fades out medially: the part of the shoulder over the chest keeps the spine it has
    W[ids] = W[ids] * (1 - share[ids])[:, None] / np.maximum(W[ids].sum(1, keepdims=True), 1e-9)
    for k, nm in enumerate((cl, ua, fa, hd)):
        W[ids, bidx[nm]] = new[:, k] * share[ids]
    rep[f'arm_{S}'] = {'verts': int(len(ids)), 'upper': float(Lu), 'len': float(L)}
# fingers
dg = np.load(FIT + '.digits.npz')
for key in dg.files:
    ch = key.split('|')
    if 'Finger' not in ch[0]:
        continue
    ids = dg[key]
    hd = parent[ch[0]]
    tipv = ids[np.argmax(np.linalg.norm(P[ids] - J[ch[0]], axis=1))]
    pts = [J[c] for c in ch] + [P[tipv]]
    s, d = poly_param(P[ids], pts)
    L = np.cumsum([np.linalg.norm(b - a) for a, b in zip(pts[:-1], pts[1:])])
    B = cfg['finger_blend']
    w1 = sstep(s, -B, B)                     # hand > proximal
    w2 = sstep(s, L[0] - B, L[0] + B)
    w3 = sstep(s, L[1] - B, L[1] + B)
    new = np.stack([1 - w1, w1 * (1 - w2), w2 * (1 - w3), w3], 1)
    setw(ids, [hd] + ch, new)
    rep.setdefault('fingers', {})[ch[0]] = int(len(ids))
# hand: palm skin that is no digit stays on the hand
for S in ('L', 'R'):
    fam = [b for b in bones if f' {S} Finger' in b]
    f = W[:, [bidx[b] for b in fam]].sum(1)
    done = set(np.concatenate([dg[k] for k in dg.files if f' {S} Finger' in k]).tolist())
    ids = np.array([i for i in np.nonzero(f > 0)[0] if i not in done], int)
    W[np.ix_(ids, [bidx[b] for b in fam])] = 0
    W[ids, bidx[f'Bip01 {S} Hand']] += f[ids]
# tail
tc = cfg['tail']
chain = [J[c] for c in tc['chain']]
ids = np.nonzero(body_v & (P[:, 1] > tc['y_min']) & (np.abs(P[:, 0]) < tc['half_x']) & (P[:, 2] < tc['z_max']))[0]
tipv = ids[np.argmax(P[ids, 1])]
pts = chain + [P[tipv]]
s, d = poly_param(P[ids], pts)
L = np.r_[0, np.cumsum([np.linalg.norm(b - a) for a, b in zip(pts[:-1], pts[1:])])]
B = tc['blend']
stk = []
prev = 1 - sstep(s, -B, B)            # pelvis
rows = [prev]
rem = 1 - prev
for k in range(len(chain)):
    if k + 1 < len(chain):
        w = sstep(s, L[k + 1] - B, L[k + 1] + B)
    else:
        w = np.zeros(len(s))
    rows.append(rem * (1 - w))
    rem = rem * w
setw(ids, [tc['base']] + tc['chain'], np.stack(rows, 1))
rep['tail_verts'] = int(len(ids))
# head above the chin-nape plane
hc = cfg['head']
a, b = np.array(hc['chin']), np.array(hc['nape'])
t = (b - a) / np.linalg.norm(b - a)
nrm = np.cross(t, [1, 0, 0]); nrm *= np.sign(nrm[2]) if nrm[2] else 1
d = (P - a) @ nrm
reg = (P[:, 2] > hc['z_min']) & (np.abs(P[:, 0]) < hc['half_x']) & (P[:, 1] < hc['y_max'])
ids = np.nonzero(reg & body_v)[0]
wh = sstep(d[ids], -hc['blend'], hc['blend'])
nk = bidx['Bip01 Neck']; hd = bidx['Bip01 Head']
old = W[ids].copy()
tot = old[:, nk] + old[:, hd]
W[ids] = old * (1 - wh)[:, None]
W[ids, nk] = tot * 0  # filled below
W[ids, hd] = wh
rest = 1 - W[ids].sum(1)
W[ids, nk] += np.maximum(rest, 0)
rep['head_verts'] = int((wh > 0.5).sum())
# soften the band borders on the main shell, fingers and tail keep their structure
keep = np.zeros(n, bool)
for key in dg.files:
    keep[dg[key]] = True
keep[np.nonzero(body_v & (P[:, 1] > tc['y_min'] + 0.05) & (np.abs(P[:, 0]) < tc['half_x']) & (P[:, 2] < tc['z_max']))[0]] = True
for _ in range(cfg.get('smooth', 0)):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.5 * W + 0.5 * avg
    new[keep] = W[keep]
    W = new
# flap, belt, loose pieces
for c in range(c_):
    if c == main:
        continue
    ids = np.nonzero(comp == c)[0]
    Q = P[ids]; ce = Q.mean(0)
    if abs(ce[0]) < 0.2 and len(ids) >= 80 and ce[2] < -0.13 and ce[1] < 0.05:      # flap
        h = Q[:, 2].max()
        w = sstep(h - Q[:, 2], 0.0, cfg.get('flap_top', 0.05))
        setw(ids, ['Bip01 Pelvis', 'Xpiv'], np.stack([1 - w, w], 1))
        rep['flap'] = int(len(ids))
    elif ce[2] < 0.1 and abs(ce[0]) < 0.2:                                          # belt, buckle
        setw(ids, ['Bip01 Pelvis'], np.ones((len(ids), 1)))
        rep.setdefault('belt', []).append(int(len(ids)))
    elif ce[2] > 0.15:                                                              # teeth, tuft, eyes
        setw(ids, ['Bip01 Head'], np.ones((len(ids), 1)))
        rep.setdefault('head_pieces', []).append(int(len(ids)))
    else:                                                                           # bracers: the bone under them
        fa = [b for b in bones if b.endswith(('Forearm', 'Hand')) and np.sign(J[b][0]) == np.sign(ce[0])]
        fb = max(fa, key=lambda b: 1 if b.endswith('Forearm') else 0)
        setw(ids, [fb], np.ones((len(ids), 1)))
        rep.setdefault('bracers', []).append(int(len(ids)))
W = np.maximum(W, 0)
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
# delete studs
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
gone = []
for c in range(c_):
    ids = np.nonzero(comp == c)[0]
    ce = P[ids].mean(0)
    if c != main and len(ids) <= cfg.get('stud_verts', 60) and ce[2] < 0.1 and abs(ce[0]) < 0.2:
        gone += [bm.verts[i] for i in ids]
rep['studs_deleted_verts'] = len(gone)
bmesh.ops.delete(bm, geom=gone, context='VERTS')
bm.to_mesh(me); bm.free()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
rep.update(verts=len(me.vertices), tris=len(me.polygons), usage={bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0.5).any()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps({k: v for k, v in rep.items() if k != 'usage'}))
