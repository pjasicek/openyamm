"""Weights by part, from the geometry (no heat): the figure is simple tubes round MM9's joints. Args: <asm npz> <rig json> <labels npy> <out npz>
Robe: bilinear on the lattice bones in (theta, z); those bones are keyed from MM9's legs and tail (robe_keys.py)."""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import half_pairs, ROBE_ROWS, ROBE_COLS, robe_bone
J_, R_, L_, OUT = sys.argv[1:5]
D = np.load(J_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
R = json.load(open(R_)); JJ = {k: np.array(v) for k, v in R['joints'].items()}; F = R['fingers']; labels = np.load(L_)
names = []
def B(n):
    if n not in names: names.append(n)
    return names.index(n)
for n in JJ: B(n)
for s in 'LR':
    for f in range(5):
        for k in ('', '1', '2'): B(f'Bip01 {s} Finger{f}{k}')
for c in range(ROBE_COLS):
    for r in range(len(ROBE_ROWS)): B(robe_bone(c, r))
W = np.zeros((len(co), len(names)))
P = lambda n: comp == pid[n]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
ix = lambda n: names.index(n)
def chain(mask, zs, bones):
    """piecewise blends along z: bones[k] below zs[k], blended over +-0.035 round each z"""
    q = np.where(mask)[0]; z = co[q, 2]; w = np.zeros((len(q), len(bones)))
    w[:, 0] = 1
    for k, zc in enumerate(zs):
        u = ss(z, zc - 0.04, zc + 0.04)
        w[:, k + 1] = u; w[:, :k + 1] *= (1 - u)[:, None]
    for k, b in enumerate(bones): W[q, ix(b)] = w[:, k]
# trunk
trunk = P('torso') | P('neckin') | P('trim')
chain(trunk, [1.31, 1.40, 1.54], ['Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Neck'])
# the collar stands on the shoulders: it follows the neck only part way
col = trunk & (co[:, 2] > 1.50); u = 0.65 * ss(co[:, 2], 1.56, 1.66)
W[col] = 0; W[col, ix('Bip01 Spine2')] = 1 - u[col]; W[col, ix('Bip01 Neck')] = u[col]
# shoulders: the yoke corners ride the clavicles
for s, sgn in (('L', 1), ('R', -1)):
    v = trunk & (co[:, 0] * sgn > 0.04) & (co[:, 2] > 1.30) & (co[:, 2] < 1.60)
    u = 0.7 * ss(co[:, 0] * sgn, 0.05, 0.19) * ss(co[:, 2], 1.32, 1.47)
    W[v] = W[v] * (1 - u[v])[:, None]; W[v, ix(f'Bip01 {s} Clavicle')] += u[v]
# head
hd = P('eyes') | P('teeth') | P('plug'); W[hd, ix('Bip01 Head')] = 1
h = P('head'); u = ss(co[:, 2] - 0.5 * (co[:, 1] + 0.02), float(os.environ.get('NK0', '1.555')), float(os.environ.get('NK1', '1.625')))
W[h, ix('Bip01 Neck')] = 1 - u[h]; W[h, ix('Bip01 Head')] = u[h]
# belt ring and what hangs on it
b = P('belt') | P('buckle'); W[b, ix('Bip01 Spine')] = 0.6; W[b, ix('Bip01 Pelvis')] = 0.4
W[P('pendant'), ix('Bip01 Spine2')] = 1
# arms
for s, sgn in (('L', 1), ('R', -1)):
    pre = f'Bip01 {s} '
    S_, E_, H_ = JJ[pre + 'UpperArm'], JJ[pre + 'Forearm'], JJ[pre + 'Hand']
    a = (H_ - S_) / np.linalg.norm(H_ - S_); se = (E_ - S_) @ a
    v = (P('sleeves') | P('slining') | P('cuffs')) & (co[:, 0] * sgn > 0)
    t = (co - S_) @ a
    u0 = ss(t, -0.05, 0.13); u1 = ss(t, se - 0.09, se + 0.09)
    W[v, ix(pre + 'Clavicle')] = (1 - u0)[v]; W[v, ix(pre + 'UpperArm')] = (u0 * (1 - u1))[v]; W[v, ix(pre + 'Forearm')] = (u0 * u1)[v]
    W[P('cuffs') & (co[:, 0] * sgn > 0)] = 0; W[P('cuffs') & (co[:, 0] * sgn > 0), ix(pre + 'Forearm')] = 1
    hand = P('hands') & (co[:, 0] * sgn > 0)
    W[hand, ix(pre + 'Hand')] = 1
    for fi in range(5):
        p = np.array(F[str(fi)]) * [sgn, 1, 1]
        fv = np.where(hand & (labels == fi + 1))[0]
        d1 = (p[1] - p[0]) / np.linalg.norm(p[1] - p[0]); d2 = (p[2] - p[1]) / np.linalg.norm(p[2] - p[1])
        x = co[fv]
        wd = 0.035 if fi == 0 else 0.012
        wb = 0.03 if fi == 0 else 0.012
        u_a = ss((x - p[0]) @ d1, -wd, wd); u_b = ss((x - p[1]) @ d1, -wb, wb); u_c = ss((x - p[2]) @ d2, -wb * 0.8, wb * 0.8)
        W[fv] = 0
        W[fv, ix(pre + 'Hand')] = 1 - u_a
        W[fv, ix(f'{pre}Finger{fi}')] = u_a * (1 - u_b)
        W[fv, ix(f'{pre}Finger{fi}1')] = u_a * u_b * (1 - u_c)
        W[fv, ix(f'{pre}Finger{fi}2')] = u_a * u_b * u_c
        # the palm next to the knuckle shares a little
        pv = np.where(hand & (labels == 0))[0]
        d = np.linalg.norm(co[pv] - p[0], axis=1); u = 0.5 * (1 - ss(d, 0.0, 0.03))
        pick = pv[u > 0.01]; uu = u[u > 0.01]
        W[pick] = W[pick] * (1 - uu)[:, None]; W[pick, ix(f'{pre}Finger{fi}')] += uu
    fv = P('feet') & (co[:, 0] * sgn > 0); u = ss(co[:, 2], 0.14, 0.22)
    W[fv, ix(pre + 'Foot')] = (1 - u)[fv]; W[fv, ix(pre + 'Calf')] = u[fv]
# robe
rv = np.where(P('robe') | P('rlining'))[0]
th = np.arctan2(co[rv, 0], -co[rv, 1]) % (2 * np.pi)          # 0 front, +pi/2 figure's left
cf = th / (2 * np.pi) * ROBE_COLS; c0 = np.floor(cf).astype(int) % ROBE_COLS; c1 = (c0 + 1) % ROBE_COLS; fc = cf - np.floor(cf)
zr = np.array(ROBE_ROWS); z = co[rv, 2]
TOP = 1.17
for i, v in enumerate(rv):
    if z[i] >= zr[0]:
        u = (z[i] - zr[0]) / (TOP - zr[0]); u = u * u * (3 - 2 * u)
        W[v, ix('Bip01 Pelvis')] = u * 0.4; W[v, ix('Bip01 Spine')] = u * 0.6
        W[v, ix(robe_bone(c0[i], 0))] = (1 - u) * (1 - fc[i]); W[v, ix(robe_bone(c1[i], 0))] = (1 - u) * fc[i]
        continue
    r0 = int(np.searchsorted(-zr, -z[i], side='right')) - 1; r0 = min(r0, len(zr) - 2); u = (zr[r0] - z[i]) / (zr[r0] - zr[r0 + 1])
    W[v, ix(robe_bone(c0[i], r0))] = (1 - u) * (1 - fc[i]); W[v, ix(robe_bone(c1[i], r0))] = (1 - u) * fc[i]
    W[v, ix(robe_bone(c0[i], r0 + 1))] = u * (1 - fc[i]); W[v, ix(robe_bone(c1[i], r0 + 1))] = u * fc[i]
# the lining's cap centre sits on the tube's axis: its azimuth means nothing, it hangs on four columns
cv = np.where(P('rlining') & (np.hypot(co[:, 0], co[:, 1] - co[P('rlining') & (co[:, 2] > 0.55)][:, 1].mean()) < 0.06) & (co[:, 2] > 0.55))[0]
for v in cv:
    W[v] = 0
    for c in (0, 3, 6, 9): W[v, ix(robe_bone(c, 1))] = 0.25
print('cap centre verts', len(cv))
# half joints
pairs = half_pairs()
names += [h_ for h_, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]
for h_, c, _, ps in pairs:
    ic = ix(c); ip = [ix(x) for x in ps]
    a_ = W[:, ip].sum(1); b_ = W[:, ic]; m_ = np.minimum(a_, b_)
    sel = m_ > 1e-4
    W[sel, ix(h_)] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a_[sel])[:, None]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww = np.where(ww < 0.012, 0, ww); ww /= ww.sum(1, keepdims=True)
print('max influences used', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()), {pn[k]: int((W[comp == k].sum(1) < 1e-5).sum()) for k in range(len(pn)) if (W[comp == k].sum(1) < 1e-5).any()})
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
