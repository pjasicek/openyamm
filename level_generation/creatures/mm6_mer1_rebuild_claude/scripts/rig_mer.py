"""Weight the fitted MM6 merchant to the MM9 HIGHWAYMAN/FIGHTERBASE skeleton by structure (copy of mm6_thf_rebuild_claude/scripts/rig_thf.py):
torso bands, arm bands, head above a chin-nape plane, leg bands. The knee-length tunic skirt (part 7) hangs on a closed ring of chains
`Robe_<k>_<j>` (16 columns x 4 bones from the belt to the hem, children of Bip01 Spine, keyed per frame by robe_keys.py); weights bilinear
in (angle, height) so neighbouring columns blend smoothly. Cap on the head; belt and studs on the Spine; the pouch copies the skin under its top.
Labels: 1 torso + sleeves, 2 face/head, 3 cap, 4 hand, 5 legs, 6 boot foot, 7 tunic skirt, 10 pouch, 12 studs, 13 belt.
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
# ---------------------------------------------------------------- robe chains (closed ring)
YC = 0.0
cv = np.nonzero(vp == 7)[0]
th_v = np.degrees(np.arctan2(P[cv, 0], P[cv, 1] - YC)); r_v = np.hypot(P[cv, 0], P[cv, 1] - YC)
ZTOP = float(P[cv, 2].max()); ZBOT = float(P[cv, 2].min())
MAIN = [-180 + 11.25 + 22.5 * k for k in range(16)]
LV_MAIN = [ZTOP - 0.02, ZTOP - 0.20, ZTOP - 0.37, ZTOP - 0.53, ZBOT - 0.01]


def radius_at(th, z):
    for dt, dz in ((12, 0.05), (18, 0.08), (25, 0.12)):
        dth = (th_v - th + 180) % 360 - 180
        m = (np.abs(dth) < dt) & (np.abs(P[cv, 2] - z) < dz)
        if m.sum() >= 3: return float(np.median(r_v[m]))
    return None


COLS = []
for th in MAIN:
    lv = LV_MAIN
    pts = []
    for z in lv:
        r = radius_at(th, z)
        if r is None: r = pts[-1][1] if pts else 0.2
        pts.append((z, r - 0.006))                     # the chain line just inside the cloth
    rs = np.array([p[1] for p in pts]); rs[1:-1] = 0.5 * rs[1:-1] + 0.25 * (rs[:-2] + rs[2:])
    joints = [np.array([np.sin(np.radians(th)) * r, YC + np.cos(np.radians(th)) * r, z]) for (z, _), r in zip(pts, rs)]
    k = len(COLS)
    COLS.append(dict(th=th, lv=lv, joints=joints, names=[f'Robe_{k:02d}_{j}' for j in range(len(lv) - 1)]))
print('RIG robe top', round(ZTOP, 3), 'hem', round(ZBOT, 3))
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
for k, d in PIV.items():
    e = eb[B + k]; v = Mi.to_3x3() @ Vector(d); e.head += v; e.tail += v
s3 = eb[B + 'Spine']
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


SP = [('Spine', 0.105), ('Spine1', 0.23), ('Spine2', 0.35), ('Spine3', 0.48)]


def torso(ids, scale=None):
    z = P[ids, 2]; ax = np.abs(P[ids, 0]); sc = np.ones(len(ids)) if scale is None else scale
    W_ = np.zeros((len(ids), 4))
    hs = [h for _, h in SP]
    W_[:, 0] = 1 - sstep(z, hs[0], hs[1])
    W_[:, 1] = sstep(z, hs[0], hs[1]) * (1 - sstep(z, hs[1], hs[2]))
    W_[:, 2] = sstep(z, hs[1], hs[2]) * (1 - sstep(z, hs[2], hs[3]))
    W_[:, 3] = sstep(z, hs[2], hs[3])
    wc = W_[:, 3] * sstep(ax, 0.09, 0.19) * sstep(z, 0.40, 0.47)
    for k, (nm, _) in enumerate(SP):
        add(ids, B + nm, sc * (W_[:, k] - (wc if k == 3 else 0)))
    for s, sx in (('R', -1), ('L', 1)):
        m = np.sign(P[ids, 0]) == sx
        W[ids[m], bidx[f'{B}{s} Clavicle']] += (sc * wc)[m]


# head plane: above it the head; the neck below it, then the chest
HA, HB = np.array([0, -0.06, 0.585]), np.array([0, 0.16, 0.60])
tv = (HB - HA) / np.linalg.norm(HB - HA); HN = np.cross(tv, [1, 0, 0]); HN *= np.sign(HN[2])


def head_neck(ids, w_all, lo=-0.02, hi=0.02):
    wh = sstep((P[ids] - HA) @ HN, lo, hi)
    wb = (1 - wh) * (1 - sstep(P[ids, 2], 0.48, 0.56))
    add(ids, B + 'Head', w_all * wh); add(ids, B + 'Spine3', w_all * wb); add(ids, B + 'Neck', w_all * (1 - wh - wb))


# torso shell (jerkin, sleeves, neck, the skull under the hood): torso bands, the arms, the head above the plane
ids = np.nonzero(vp == 1)[0]
up = sstep(P[ids, 2], 0.49, 0.56)                            # neck and skull: head/neck rule
torso(ids, 1 - up)
head_neck(ids, up)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd, cl = [J[f'{B}{s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & (vp == 1))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua)
    wa = sstep(t, -0.065, 0.075) * sstep(np.abs(P[q, 0]), 0.15, 0.22) * (1 - sstep(d, 0.12, 0.16)) * (1 - sstep(P[q, 2], 0.53, 0.58))
    we = sstep(t, Lu - 0.06, Lu + 0.06)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa * (1 - we)); add(q, f'{B}{s} Forearm', wa * we)
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'{B}{s} Hand', 1.0)
add(np.nonzero(vp == 3)[0], B + 'Head', 1.0)
# face
q = np.nonzero(vp == 2)[0]
head_neck(q, np.ones(len(q)))
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
# ---------------------------------------------------------------- robe: chains by (angle, height); the top ring on the Spine (belt)
q = cv
z = P[q, 2]; th = th_v
cw = np.zeros((len(q), len(COLS)))
angs_all = np.array([c['th'] for c in COLS], float)
for i in range(len(q)):
    a_ = angs_all; t_ = th[i]
    if t_ <= a_[0] or t_ >= a_[-1]:
        lo, hi = len(COLS) - 1, 0; span = (a_[0] + 360) - a_[-1]
        u = ((t_ - a_[-1]) % 360) / span
        u = u * u * (3 - 2 * u); cw[i, lo] = 1 - u; cw[i, hi] = u
        continue
    k = np.searchsorted(a_, t_) - 1
    u = (t_ - a_[k]) / (a_[k + 1] - a_[k]); u = u * u * (3 - 2 * u)
    cw[i, k] = 1 - u; cw[i, k + 1] = u
chain = np.zeros(len(q))
for k, c in enumerate(COLS):
    lv = c['lv']; nb = len(lv) - 1
    croot = 1 - sstep(z, lv[0] - 0.07, lv[0] + 0.0)
    rw = np.zeros((len(q), nb))
    hb = 0.06
    for j in range(nb):
        top = 1.0 if j == 0 else sstep(lv[j] + hb - z, 0, 2 * hb)
        bot = 1.0 if j == nb - 1 else 1 - sstep(lv[j + 1] + hb - z, 0, 2 * hb)
        rw[:, j] = top * bot
    rw /= np.maximum(rw.sum(1, keepdims=True), 1e-9)
    for j, nm in enumerate(c['names']):
        add(q, nm, cw[:, k] * croot * rw[:, j])
    chain += cw[:, k] * croot
add(q, B + 'Spine', 1 - chain)
q = np.nonzero(np.isin(vp, [12, 13]))[0]; add(q, B + 'Spine', 1.0)
# soften the bands inside each garment (2 passes); hands, bracers, cloak chains kept
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [3, 4, 7, 10, 12, 13])
    new[keep] = W[keep]
    W = new
# pouch: copy the skin under its top (belt-level skirt)
host = np.nonzero(np.isin(vp, [1, 7]))[0]
for c in np.unique(comp[vp == 10]):
    ids = np.nonzero(comp == c)[0]
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
    if not np.any(W[:, bidx[g.name]] > 0) and not g.name.startswith('Robe_'): body.vertex_groups.remove(g)
body.parent = arm; body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
cols_json = [dict(th=c['th'], lv=c['lv'], names=c['names'], joints=[j.tolist() for j in c['joints']]) for c in COLS]
json.dump(cols_json, open(OUT + '.robe.json', 'w'), indent=0)
rep = dict(verts=n, tris=len(me.polygons), bones=len(bones), usage={bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0.5).any()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep)[:900])
