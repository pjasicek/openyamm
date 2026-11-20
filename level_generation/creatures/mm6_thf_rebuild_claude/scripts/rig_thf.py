"""Weight the fitted MM6 thief to the MM9 HIGHWAYMAN skeleton by structure (rules of mm9_highwayman_claude/scripts/rig_hw.py): torso bands, arm bands,
head above a chin-nape plane, leg bands, garments copied from the skin under them. Jerkin skirt on eight hinge bones `Skirt_*` at the belt (children
of Bip01 Spine, keyed by skirt_keys.py). The cloak (part 14, hood included) on chains `Cloak_<k>_<j>`: ten main columns round the back and sides
(4 bones, root ring at the shoulders down to the hem) and four short front-mantle columns (2 bones), children of Bip01 Spine3, keyed by
cloak_keys.py; weights bilinear in (angle, height) so neighbouring columns blend smoothly; the hood is the head's, the neck ring and the shoulder
caps the torso's (and a share of the upper arm).
Labels: 1 torso, 2 face, 4 hand, 5 legs, 6 boot, 7 jerkin skirt, 8 bracer, 9 strap, 10 pouch, 11 sheath, 12 buckle, 14 cloak + hood.
Args: <fit blend> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
FIT, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
for o in list(bpy.data.objects):
    if o not in (arm, body): bpy.data.objects.remove(o)
B = 'Bip01 '
PIV = {'L Calf': (0, 0.03, 0), 'R Calf': (0, 0.03, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.025, 0), 'R Thigh': (0, -0.025, 0)}
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
for k, d in PIV.items(): J[B + k] = J[B + k] + np.array(d)
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
# ---------------------------------------------------------------- jerkin skirt hinges (rig_hw.py)
sk = np.nonzero(vp == 7)[0]
ztop = P[sk, 2].max(); ring = sk[P[sk, 2] > ztop - 0.06]
HZ = ztop - 0.04
cx, cy = 0.0, 0.5 * (P[ring, 1].min() + P[ring, 1].max()); rx, ry = 0.5 * np.ptp(P[ring, 0]), 0.5 * np.ptp(P[ring, 1])
SANG = np.radians([-112.5, -67.5, -22.5, 22.5, 67.5, 112.5, 157.5, -157.5])
SRING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SFL', 'Skirt_SBL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SBR', 'Skirt_SFR']
HINGES = {nm: np.array([cx + rx * 0.9 * np.cos(a), cy + ry * 0.9 * np.sin(a), HZ]) for nm, a in zip(SRING, SANG)}
print('RIG skirt top', round(ztop, 3), 'hinge z', round(HZ, 3), 'centre y', round(cy, 3), 'radii', round(rx, 3), round(ry, 3))
# ---------------------------------------------------------------- cloak chains
YC = 0.06
cv = np.nonzero(vp == 14)[0]
th_v = np.degrees(np.arctan2(P[cv, 0], P[cv, 1] - YC)); r_v = np.hypot(P[cv, 0], P[cv, 1] - YC)
MAIN = [-100, -78, -55, -32, -10, 10, 32, 55, 78, 100]
FRONT = [-155, -130, 130, 155]
LV_MAIN = [0.46, 0.16, -0.16, -0.50, -0.84]
LV_FRONT = [0.47, 0.36, 0.25]


def radius_at(th, z):
    for dt, dz in ((12, 0.05), (18, 0.08), (25, 0.12)):
        m = (np.abs(th_v - th) < dt) & (np.abs(P[cv, 2] - z) < dz)
        if m.sum() >= 3: return float(np.median(r_v[m]))
    return None


COLS = []
for th in MAIN + FRONT:
    lv = LV_MAIN if th in MAIN else LV_FRONT
    pts = []
    for z in lv:
        r = radius_at(th, z)
        if r is None: r = pts[-1][1] if pts else 0.2
        pts.append((z, r))
    rs = np.array([p[1] for p in pts]); rs[1:-1] = 0.5 * rs[1:-1] + 0.25 * (rs[:-2] + rs[2:])      # a smoother chain
    joints = [np.array([np.sin(np.radians(th)) * r, YC + np.cos(np.radians(th)) * r, z]) for (z, _), r in zip(pts, rs)]
    k = len(COLS)
    COLS.append(dict(th=th, lv=lv, joints=joints, names=[f'Cloak_{k:02d}_{j}' for j in range(len(lv) - 1)]))
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
for k, d in PIV.items():
    e = eb[B + k]; v = Mi.to_3x3() @ Vector(d); e.head += v; e.tail += v
sp = eb[B + 'Spine']; Rt = sp.matrix.to_3x3()
for nm, h in HINGES.items():
    b = eb.new(nm); hp = Mi @ Vector(h)
    b.head = hp; b.tail = hp + Rt.col[1] * 0.08; b.align_roll(Rt.col[2]); b.parent = sp; b.use_connect = False; b.use_deform = True
s3 = eb[B + 'Spine3']
for c in COLS:
    par = s3
    for j, nm in enumerate(c['names']):
        b = eb.new(nm); h0 = Mi @ Vector(c['joints'][j]); h1 = Mi @ Vector(c['joints'][j + 1])
        b.head = h0; b.tail = h1
        out = Vector((np.sin(np.radians(c['th'])), np.cos(np.radians(c['th'])), 0.0))
        b.align_roll(Mi.to_3x3() @ out)
        b.parent = par; b.use_connect = False; b.use_deform = True; par = b
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in arm.data.bones]; bidx = {b: i for i, b in enumerate(bones)}
for nm, h in HINGES.items(): J[nm] = np.array(h)
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


SP = [('Spine', 0.105), ('Spine1', 0.24), ('Spine2', 0.37), ('Spine3', 0.52)]


def torso(ids, scale=None):
    z = P[ids, 2]; ax = np.abs(P[ids, 0]); sc = np.ones(len(ids)) if scale is None else scale
    W_ = np.zeros((len(ids), 4))
    hs = [h for _, h in SP]
    W_[:, 0] = 1 - sstep(z, hs[0], hs[1])
    W_[:, 1] = sstep(z, hs[0], hs[1]) * (1 - sstep(z, hs[1], hs[2]))
    W_[:, 2] = sstep(z, hs[1], hs[2]) * (1 - sstep(z, hs[2], hs[3]))
    W_[:, 3] = sstep(z, hs[2], hs[3])
    wc = W_[:, 3] * sstep(ax, 0.09, 0.19) * sstep(z, 0.42, 0.50)
    for k, (nm, _) in enumerate(SP):
        add(ids, B + nm, sc * (W_[:, k] - (wc if k == 3 else 0)))
    for s, sx in (('R', -1), ('L', 1)):
        m = np.sign(P[ids, 0]) == sx
        W[ids[m], bidx[f'{B}{s} Clavicle']] += (sc * wc)[m]


# head plane: above it the head; the neck below it, then the chest
HA, HB = np.array([0, -0.045, 0.652]), np.array([0, 0.175, 0.69])
tv = (HB - HA) / np.linalg.norm(HB - HA); HN = np.cross(tv, [1, 0, 0]); HN *= np.sign(HN[2])


def head_neck(ids, w_all, lo=-0.02, hi=0.02):
    wh = sstep((P[ids] - HA) @ HN, lo, hi)
    wb = (1 - wh) * (1 - sstep(P[ids, 2], 0.53, 0.62))
    add(ids, B + 'Head', w_all * wh); add(ids, B + 'Spine3', w_all * wb); add(ids, B + 'Neck', w_all * (1 - wh - wb))


# torso shell (jerkin, sleeves, neck, the skull under the hood): torso bands, the arms, the head above the plane
ids = np.nonzero(vp == 1)[0]
up = sstep(P[ids, 2], 0.53, 0.60)                            # neck and skull: head/neck rule
torso(ids, 1 - up)
head_neck(ids, up)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd, cl = [J[f'{B}{s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & (vp == 1))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua)
    wa = sstep(t, -0.065, 0.075) * sstep(np.abs(P[q, 0]), 0.13, 0.20) * (1 - sstep(P[q, 2], 0.55, 0.60))
    we = sstep(t, Lu - 0.06, Lu + 0.06)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa * (1 - we)); add(q, f'{B}{s} Forearm', wa * we)
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'{B}{s} Hand', 1.0)
    q = np.nonzero((vp == 8) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'{B}{s} Forearm', 1.0)
# face
q = np.nonzero(vp == 2)[0]
head_neck(q, np.ones(len(q)))
# skirt: hinges round the ring, by height
q = np.nonzero(vp == 7)[0]
ang = np.arctan2(P[q, 1] - cy, P[q, 0] - cx)
r = sstep(HZ + 0.015 - P[q, 2], 0.0, 0.11)
A = np.sort(SANG); order = np.argsort(SANG)
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
A2 = np.r_[A, A[0] + 2 * np.pi]
sw = np.zeros((len(q), 8))
for k in range(8):
    mm = (aa >= A2[k]) & (aa < A2[k + 1])
    u = sstep((aa[mm] - A2[k]) / (A2[k + 1] - A2[k]), 0, 1)
    sw[mm, k] = 1 - u; sw[mm, (k + 1) % 8] = u
for k in range(8):
    add(q, SRING[order[k]], sw[:, k] * r)
add(q, B + 'Spine', 1 - r)
# legs, boots
for s, sx in (('R', -1), ('L', 1)):
    th, ca, fo, to = [J[f'{B}{s} {x}'] for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
    q = np.nonzero((vp == 5) & (np.sign(P[:, 0]) == sx))[0]
    t, d = poly_param(P[q], [th, ca, fo])
    Lt = np.linalg.norm(ca - th)
    wt = sstep(t, -0.07, 0.06) * sstep(np.abs(P[q, 0]), 0.0, 0.03)
    wk = sstep(t, Lt - 0.075, Lt + 0.075)
    add(q, f'{B}{s} Thigh', wt * (1 - wk)); add(q, f'{B}{s} Calf', wt * wk)
    add(q, B + 'Pelvis', 1 - wt)
    q = np.nonzero((vp == 6) & (np.sign(P[:, 0]) == sx))[0]
    z = P[q, 2]
    wf = 1 - sstep(z, fo[2] - 0.03, fo[2] + 0.05)
    fd = to[:2] - fo[:2]; fd = fd / np.linalg.norm(fd)
    al = (P[q, :2] - to[:2]) @ fd
    wy = sstep(al, -0.02, 0.03) * (1 - sstep(z, to[2] + 0.03, to[2] + 0.07))
    add(q, f'{B}{s} Calf', 1 - wf); add(q, f'{B}{s} Foot', wf * (1 - wy)); add(q, f'{B}{s} Toe0', wf * wy)
q = np.nonzero((vp == 5) & (P[:, 0] == 0))[0]; add(q, B + 'Pelvis', 1.0)
# ---------------------------------------------------------------- cloak + hood
q = cv
z = P[q, 2]; th = th_v; ax = np.abs(P[q, 0])
# hood/neck/shoulder cap (above the chain roots): head above the plane (wider blend), the neck ring, the shoulder caps on the torso and arm
c_main = 1 - sstep(z, LV_MAIN[0] - 0.06, LV_MAIN[0] + 0.04)
cw = np.zeros((len(q), len(COLS)))                          # column weights
isfront_ok = z >= 0.30
angs_all = np.array([c['th'] for c in COLS], float)
for i in range(len(q)):
    use = [k for k, c in enumerate(COLS) if c['th'] in MAIN or isfront_ok[i]]
    a_ = angs_all[use]; o_ = np.argsort(a_); a_ = a_[o_]; use = [use[k] for k in o_]
    t_ = th[i]
    if t_ <= a_[0] or t_ >= a_[-1]:
        if len(use) == len(COLS):                          # the closed front of the mantle: wrap between the two inner-most front columns
            lo, hi = use[-1], use[0]; span = (a_[0] + 360) - a_[-1]
            u = ((t_ - a_[-1]) % 360) / span
            u = u * u * (3 - 2 * u); cw[i, lo] = 1 - u; cw[i, hi] = u
        else:
            cw[i, use[0] if t_ <= a_[0] else use[-1]] = 1
        continue
    k = np.searchsorted(a_, t_) - 1
    u = (t_ - a_[k]) / (a_[k + 1] - a_[k]); u = u * u * (3 - 2 * u)
    cw[i, use[k]] = 1 - u; cw[i, use[k + 1]] = u
chain = np.zeros(len(q))
for k, c in enumerate(COLS):
    lv = c['lv']; nb = len(lv) - 1
    croot = 1 - sstep(z, lv[0] - 0.06, lv[0] + 0.04)
    rw = np.zeros((len(q), nb))
    hb = 0.07
    for j in range(nb):
        top = 1.0 if j == 0 else sstep(lv[j] + hb - z, 0, 2 * hb)
        bot = 1.0 if j == nb - 1 else 1 - sstep(lv[j + 1] + hb - z, 0, 2 * hb)
        rw[:, j] = top * bot
    rw /= np.maximum(rw.sum(1, keepdims=True), 1e-9)
    for j, nm in enumerate(c['names']):
        add(q, nm, cw[:, k] * croot * rw[:, j])
    chain += cw[:, k] * croot
rest = 1 - chain
# the part above the chains: hood on the head (wide blend), neck ring on neck/Spine3, shoulder caps on the torso bands + a share of the upper arm
wh = sstep((P[q] - HA) @ HN, -0.05, 0.02) * sstep(z, 0.58, 0.66)
add(q, B + 'Head', rest * wh)
low = rest * (1 - wh)
wn = sstep(z, 0.52, 0.60) * (1 - sstep(ax, 0.10, 0.17))
add(q, B + 'Neck', low * wn)
low2 = low * (1 - wn)
for s, sx in (('R', -1), ('L', 1)):
    m = np.sign(P[q, 0]) == sx
    wa = 0.5 * sstep(ax, 0.15, 0.24)
    add(q[m], f'{B}{s} UpperArm', (low2 * wa)[m]); add(q[m], f'{B}{s} Clavicle', (low2 * (1 - wa) * sstep(ax, 0.06, 0.14))[m])
    add(q[m], B + 'Spine3', (low2 * (1 - wa) * (1 - sstep(ax, 0.06, 0.14)))[m])
# soften the bands inside each garment (2 passes); hands, bracers, cloak chains kept
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [4, 8, 9, 10, 11, 12, 14])
    new[keep] = W[keep]
    W = new
# strap, pouch, sheath, buckle: copy the skin under them (torso or skirt)
host = np.nonzero(np.isin(vp, [1, 7]))[0]
for pc in (9, 10, 11, 12):
    for c in np.unique(comp[vp == pc]):
        ids = np.nonzero(comp == c)[0]
        if pc == 9:                                       # the strap runs over the chest: per vertex
            for i in ids:
                k = host[np.argsort(np.linalg.norm(P[host] - P[i], axis=1))[:4]]
                W[i] = W[k].mean(0)
        else:
            top = P[ids, 2].max()
            k = host[np.argsort(np.linalg.norm(P[host] - P[ids][P[ids, 2] > top - 0.03].mean(0), axis=1))[:6]]
            W[ids] = W[k].mean(0)
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
    if not np.any(W[:, bidx[g.name]] > 0) and not g.name.startswith('Cloak_'): body.vertex_groups.remove(g)
body.parent = arm; body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
cols_json = [dict(th=c['th'], lv=c['lv'], names=c['names'], joints=[j.tolist() for j in c['joints']]) for c in COLS]
json.dump(cols_json, open(OUT + '.cloak.json', 'w'), indent=0)
rep = dict(verts=n, tris=len(me.polygons), bones=len(bones), usage={bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0.5).any()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep)[:900])
