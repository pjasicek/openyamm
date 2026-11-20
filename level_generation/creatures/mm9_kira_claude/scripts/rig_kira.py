"""Kira (from mm9_njam_claude/scripts/rig_nj.py): weights to KIRA.abc's skeleton by structure. Torso bands between the spine bones, arm
bands along the arm (sleeves, vambraces), head above a chin-nape plane with a neck band, leg bands with the boot on Foot/Toe0. Rigid
copies (one weight row per piece, the average of the shell under it): belt + buckle, medallion. Per-vertex copies of the surface under
them: pauldron lames (shell), knee cops (legs), tasset (skirt). Hair: the cap round the skull rigid on the Head, the long back and side
hair on MM9's own back-hair chain Yhair..YhC by position along it; braid on MM9's Yponybase..YpC chain (moved onto it by build_braid.py).
KIRA.abc has no skirt bones: six hinges (`Bone06/14/18/02/10/22`, names and layout as NJAM.abc's so skirt_keys.py applies) are added
under Bip01 Spine on the mail skirt's top ring, weighted round the ring and by height, keyed by skirt_keys.py.
Hinge pivots: knee and hip toward the inside of the bend, elbow toward the outside.
Args: <braid blend> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
FIT, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
for o in list(bpy.data.objects):
    if o not in (arm, body): bpy.data.objects.remove(o)
B = 'Bip01 '
PIV = {'L Calf': (0, 0.04, 0), 'R Calf': (0, 0.04, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.02, 0), 'R Thigh': (0, -0.02, 0)}
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
for k, d in PIV.items(): J[B + k] = J[B + k] + np.array(d)
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
sk = np.nonzero(vp == 7)[0]
ztop = P[sk, 2].max(); ring = sk[P[sk, 2] > ztop - 0.04]
HZ = ztop - 0.02
cx, cy = 0.0, 0.5 * (P[ring, 1].min() + P[ring, 1].max()); rx, ry = 0.5 * np.ptp(P[ring, 0]), 0.5 * np.ptp(P[ring, 1])
ANG = np.radians([-90.0, -45.0, 50.0, 90.0, 130.0, -135.0])
RING = ['Bone06', 'Bone14', 'Bone18', 'Bone02', 'Bone10', 'Bone22']          # front centre, then round by the figure's left
HINGES = {nm: np.array([cx + rx * 0.85 * np.cos(a), cy + ry * 0.85 * np.sin(a), HZ]) for nm, a in zip(RING, ANG)}
print('RIG skirt top', round(ztop, 3), 'hinge z', round(HZ, 3), 'centre y', round(cy, 3), 'radii', round(rx, 3), round(ry, 3), 'bottom', round(P[sk, 2].min(), 3))
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
for k, d in PIV.items():
    e = eb[B + k]; v = Mi.to_3x3() @ Vector(d); e.head += v; e.tail += v
for nm, h in HINGES.items():
    e = eb.new(nm); e.head = Mi @ Vector(h); e.tail = Mi @ Vector(h + np.array([0, 0, -0.1])); e.roll = 0.0
    e.parent = eb[B + 'Spine']
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in arm.data.bones]; bidx = {b: i for i, b in enumerate(bones)}
for nm, h in HINGES.items(): J[nm] = np.array(h)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
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


# spine hats centred on each bone's middle
SP = [('Spine', 0.15), ('Spine1', 0.29), ('Spine2', 0.40), ('Spine3', 0.51)]
def torso(ids):
    z = P[ids, 2]; ax = np.abs(P[ids, 0])
    W_ = np.zeros((len(ids), 4))
    hs = [h for _, h in SP]
    W_[:, 0] = 1 - sstep(z, hs[0], hs[1])
    W_[:, 1] = sstep(z, hs[0], hs[1]) * (1 - sstep(z, hs[1], hs[2]))
    W_[:, 2] = sstep(z, hs[1], hs[2]) * (1 - sstep(z, hs[2], hs[3]))
    W_[:, 3] = sstep(z, hs[2], hs[3])
    wc = W_[:, 3] * sstep(ax, 0.07, 0.16) * sstep(z, 0.49, 0.57)
    for k, (nm, _) in enumerate(SP):
        add(ids, B + nm, W_[:, k] - (wc if k == 3 else 0))
    for s, sx in (('R', -1), ('L', 1)):
        m = np.sign(P[ids, 0]) == sx
        W[ids[m], bidx[f'{B}{s} Clavicle']] += wc[m]


ids = np.nonzero(vp == 1)[0]
torso(ids)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd, cl = [J[f'{B}{s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & (vp == 1))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua)
    zz = sstep(P[q, 2], 0.44, 0.55)
    wa = sstep(t, -0.08, 0.08) * sstep(np.abs(P[q, 0]), 0.12 - 0.03 * zz, 0.165 + 0.015 * zz) * (1 - sstep(d, 0.07, 0.10))
    we = sstep(t, Lu - 0.06, Lu + 0.06)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa * (1 - we)); add(q, f'{B}{s} Forearm', wa * we)
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'{B}{s} Hand', 1.0)
# mail collar: its top follows the neck a little
q = np.nonzero((vp == 1) & (P[:, 2] > 0.58) & (np.abs(P[:, 0]) < 0.10))[0]
wn = 0.4 * sstep(P[q, 2], 0.60, 0.65)
W[q] *= (1 - wn)[:, None]; add(q, B + 'Neck', wn)
# face and neck skin, eyes
q = np.nonzero(vp == 22)[0]; add(q, B + 'Head', 1.0)
q = np.nonzero(vp == 20)[0]
a, b = np.array([0, -0.075, 0.69]), np.array([0, 0.10, 0.73])
tv = (b - a) / np.linalg.norm(b - a); nrm = np.cross(tv, [1, 0, 0]); nrm *= np.sign(nrm[2])
wh = sstep((P[q] - a) @ nrm, -0.03, 0.03)
add(q, B + 'Head', wh)
wb = (1 - wh) * (1 - sstep(P[q, 2], 0.58, 0.65))
add(q, B + 'Spine3', wb); add(q, B + 'Neck', 1 - wh - wb)
# hair: the cap round the skull on the Head, the hanging hair on MM9's back-hair chain
q = np.nonzero(vp == 21)[0]
HC = [J[x] for x in ('Yhair', 'Yhpiv', 'YhA', 'YhB', 'YhC')] + [J['YhC'] + np.array([0, 0.01, -0.12])]
t, d = poly_param(P[q], HC)
cum = np.r_[0, np.cumsum([np.linalg.norm(b_ - a_) for a_, b_ in zip(HC[:-1], HC[1:])])]
names_h = ['Yhair', 'Yhpiv', 'YhA', 'YhB', 'YhC']
cap = sstep(P[q, 2], 0.66, 0.75) * 1.0
whd = np.maximum(cap, 1 - sstep(np.linalg.norm(P[q] - J[B + 'Head'] - np.array([0, -0.01, 0.07]), axis=1), 0.10, 0.13))
for k, nm in enumerate(names_h):
    lo = cum[k - 1] if k else -1.0; mid = cum[k]; hi = cum[k + 1] if k + 1 < len(cum) else 9.0
    w_ = np.where(t < mid, (t - lo) / (mid - lo), 1 - (t - mid) / (hi - mid)) if k else np.where(t < mid, 1.0, 1 - (t - mid) / (hi - mid))
    if k == len(names_h) - 1: w_ = np.where(t >= mid, 1.0, w_)
    add(q, nm, np.clip(w_, 0, 1) * (1 - whd))
add(q, B + 'Head', whd)
# braid on the Yp chain
q = np.nonzero(vp == 23)[0]
BC = [J[x] for x in ('Yponybase', 'Ypony', 'Yponypiv', 'YpA', 'YpB', 'YpC')]
BC.append(BC[-1] + (BC[-1] - BC[-2]) / np.linalg.norm(BC[-1] - BC[-2]) * 0.08)
t, d = poly_param(P[q], BC)
cum = np.r_[0, np.cumsum([np.linalg.norm(b_ - a_) for a_, b_ in zip(BC[:-1], BC[1:])])]
names_b = ['Yponybase', 'Ypony', 'Yponypiv', 'YpA', 'YpB', 'YpC']
for k, nm in enumerate(names_b):
    lo = cum[k - 1] if k else -1.0; mid = cum[k]; hi = cum[k + 1]
    w_ = np.where(t < mid, (t - lo) / (mid - lo) if k else 1.0, 1 - (t - mid) / (hi - mid))
    if k == len(names_b) - 1: w_ = np.where(t >= mid, 1.0, w_)
    add(q, nm, np.clip(w_, 0, 1))
# skirt: hinges round the ring, by height
q = np.nonzero(vp == 7)[0]
ang = np.arctan2(P[q, 1] - cy, P[q, 0] - cx)
r = sstep(HZ + 0.01 - P[q, 2], 0.0, 0.09)
A = np.sort(ANG); order = np.argsort(ANG)
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
A2 = np.r_[A, A[0] + 2 * np.pi]
sw = np.zeros((len(q), 6))
for k in range(6):
    mm = (aa >= A2[k]) & (aa < A2[k + 1])
    u = sstep((aa[mm] - A2[k]) / (A2[k + 1] - A2[k]), 0, 1)
    sw[mm, k] = 1 - u; sw[mm, (k + 1) % 6] = u
for k in range(6):
    add(q, RING[order[k]], sw[:, k] * r)
add(q, B + 'Spine', 1 - r)
# legs (leggings and boots in one part): bands down to the ankle, the boot foot on Foot/Toe0
for s, sx in (('R', -1), ('L', 1)):
    th, ca, fo, to = [J[f'{B}{s} {x}'] for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
    q = np.nonzero((vp == 5) & (P[:, 2] > fo[2] + 0.04) & ((np.sign(P[:, 0]) == sx) | (P[:, 0] == 0)))[0]
    t, d = poly_param(P[q], [th, ca, fo])
    Lt = np.linalg.norm(ca - th)
    wt = sstep(t, -0.12, 0.08) * sstep(np.abs(P[q, 0]), 0.0, 0.03)
    wk = sstep(t, Lt - 0.07, Lt + 0.07)
    if s == 'R': W[q] = 0
    else: W[q[P[q, 0] > 0]] = 0
    m = P[q, 0] == 0
    add(q, f'{B}{s} Thigh', wt * (1 - wk)); add(q, f'{B}{s} Calf', wt * wk)
    add(q[~m], B + 'Spine', (1 - wt)[~m])
    if s == 'R': add(q[m], B + 'Spine', (1 - wt)[m])
    q = np.nonzero((vp == 5) & (np.sign(P[:, 0]) == sx) & (P[:, 2] <= fo[2] + 0.04))[0]
    z = P[q, 2]
    wf = 1 - sstep(z, fo[2] - 0.03, fo[2] + 0.04)
    fd = to[:2] - fo[:2]; fd = fd / np.linalg.norm(fd)
    al = (P[q, :2] - to[:2]) @ fd
    wy = sstep(al, -0.02, 0.03) * (1 - sstep(z, to[2] + 0.03, to[2] + 0.07))
    add(q, f'{B}{s} Calf', 1 - wf); add(q, f'{B}{s} Foot', wf * (1 - wy)); add(q, f'{B}{s} Toe0', wf * wy)


def copy_from(dst_part, src_parts, rigid=False, k=4):
    src = np.nonzero(np.isin(vp, src_parts))[0]
    kd = KDTree(len(src))
    for i, v in enumerate(src): kd.insert(P[v], i)
    kd.balance()
    q = np.nonzero(vp == dst_part)[0]
    rows = np.zeros((len(q), W.shape[1]))
    for j, v in enumerate(q):
        hits = kd.find_n(P[v], k)
        ws = np.array([1.0 / (h[2] + 1e-3) for h in hits])
        rows[j] = (W[src[[h[1] for h in hits]]] * ws[:, None]).sum(0) / ws.sum()
    if rigid:
        rows[:] = rows.mean(0)
    W[q] = rows


copy_from(12, [1])                     # pauldron lames
copy_from(9, [1], rigid=True)          # belt and buckle
copy_from(10, [1], rigid=True)         # medallion
copy_from(11, [5])                     # knee cops
copy_from(13, [7])                     # tasset
# soften the bands inside each garment (2 passes)
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [4, 9, 10, 22])
    new[keep] = W[keep]
    W = new
order_ = np.argsort(-W, axis=1)
for i in range(n):
    keep = order_[i, :4]
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
