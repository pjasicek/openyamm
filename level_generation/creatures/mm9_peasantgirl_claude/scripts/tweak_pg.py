#!/usr/bin/env python3
"""Position-only tweaks after the paint (UVs, faces and weights unchanged): work/uv_tex.npz -> work/uv_tex2.npz.
- Eyeballs EYE_FWD forward (Meshy set them 7 mm behind the lid opening: from the party's height above, the parallax showed the white
  under the iris, a stare). Args: <in npz> <out npz>. Project folder."""
import os, sys
import numpy as np
IN, OUT = sys.argv[1:3]
D = dict(np.load(IN)); A = np.load('work/asm_frozen.npz')
ac, at, acomp = A['co'], A['tri'], A['comp']; hk = [str(x) for x in A['names']].index('head')
par = np.arange(len(ac))
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in at[acomp[at[:, 0]] == hk]:
    ra = find(a); par[find(b)] = ra; par[find(c)] = ra
hv = np.where(acomp == hk)[0]; roots = np.array([find(v) for v in hv]); big = np.bincount(roots).argmax()
eyev = np.zeros(len(ac), bool); eyev[hv[roots != big]] = True
FWD = float(os.environ.get('EYE_FWD', '0.003'))
sel = eyev[D['orig']]; co = D['co'].copy(); co[sel, 1] -= FWD; D['co'] = co
# lower lids raised (Meshy's lid opening runs 6 mm under the eye centre: from the party's height a stare, white or a skin-coloured lump of
# the ball under the iris): the lid ring below the eye (and its fold into the socket) goes up LID_UP and LID_FWD forward, fading out
# 1.8 eye radii from the eye axis and above the eye centre
LID = float(os.environ.get('LID_UP', '0.0040')); FWDL = float(os.environ.get('LID_FWD', '0.0010'))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
shell = (acomp == hk) & ~eyev; sv = shell[D['orig']]; n_lid = 0
for sg in (1, -1):
    q = ac[eyev & (ac[:, 0] * sg > 0)]; c = q.mean(0); r = float(np.linalg.norm(q - c, axis=1).max())
    P = co[sv]; dxz = np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
    w = (1 - ss(dxz, 1.1 * r, 2.0 * r)) * ss(c[2] - P[:, 2], 0.0, 0.002) * (P[:, 1] < c[1] + 0.2 * r) * (P[:, 0] * sg > 0)
    K = float(os.environ.get('LID_K', '0.35'))       # the lower half of the opening compressed toward the eye centre
    below = np.maximum(c[2] - P[:, 2], 0)
    P[:, 2] += (below * (1 - K)) * w; P[:, 1] -= FWDL * w; co[sv] = P; n_lid += int((w > 0.05).sum())
# shin tops (hidden under the skirt): their outer rim at the knee touched the skirt's side folds in Talk and Death (robe gate, 1 vertex,
# 1.5 / 2.5 cm); the top 8 cm narrowed toward each leg's axis, up to 30 %
lp = [str(x) for x in D['names']].index('legs'); lv = D['comp'] == lp
for sg in (1, -1):
    m = lv & (co[:, 0] * sg > 0); k = 0.40 * ss(co[m, 2], -0.30, -0.15)
    cx = np.array([0.074 * sg, -0.01]); co[np.where(m)[0], :2] = co[m, :2] + (cx - co[m, :2]) * k[:, None]
    zz = co[m, 2]; co[np.where(m)[0], 2] = np.where(zz > -0.30, -0.30 + (zz + 0.30) * 0.25, zz)   # and the knee end 12 cm lower (MM9 moves the knee by translation; robe gate)
# hairline ledge (coordinator review, 2026-11-02): the hair shell rises from 2 mm off the forehead at its front edge to 12 mm within 1.3 cm
# (a ridge / hairband at 128 px). Hair vertices within TAPER of the shell's front open edges blend toward the head surface under them
# (nearest head vertex + 1.5 mm), fully at the edge, fading out over TAPER, so the hair rises from the scalp gradually. Computed on the
# welded asm positions and carried to every UV copy (same orig), so no seam opens.
TAPER = float(os.environ.get('HAIR_TAPER', '0.035')); hp = [str(x) for x in A['names']].index('hair')
ht = at[acomp[at[:, 0]] == hp]; e_ = np.sort(np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]]), 1); u_, c_ = np.unique(e_, axis=0, return_counts=True)
bv = ac[np.unique(u_[c_ == 1].ravel())]; bv = bv[(bv[:, 2] > 0.70) & (bv[:, 1] < -0.02)]
from scipy.spatial import cKDTree
headv = ac[(acomp == hk) & ~eyev]
ha = np.where((acomp == hp) & (ac[:, 2] > 0.69) & (ac[:, 1] < 0.0))[0]
dd, _ = cKDTree(bv).query(ac[ha]); w = 0.9 * (1 - ss(dd, 0.0, TAPER))
dh, ih = cKDTree(headv).query(ac[ha]); ph = headv[ih]; dirv = ac[ha] - ph; dirv /= np.maximum(np.linalg.norm(dirv, axis=1, keepdims=True), 1e-9)
tgt = ph + dirv * 0.0015
delta = np.zeros_like(ac); delta[ha] = (tgt - ac[ha]) * w[:, None] * (dh > 0.0015)[:, None]
# chin (coordinator review): Meshy's chin comes to a faceted V in front views; head vertices under the mouth are Laplacian-smoothed
# (welded asm graph, 12 passes, feathered), positions only: the rigid-head weights are untouched
hv_all = np.where((acomp == hk) & ~eyev)[0]
cw = (1 - ss(np.abs(ac[:, 0]), 0.025, 0.045)) * (1 - ss(ac[:, 2], 0.600, 0.612)) * ss(ac[:, 2], 0.580, 0.590) * (ac[:, 1] < -0.04)      # the level neck seam (0.5703) never moves
cw[~np.isin(np.arange(len(ac)), hv_all)] = 0
ht2 = at[acomp[at[:, 0]] == hk]; E2 = np.vstack([ht2[:, [0, 1]], ht2[:, [1, 2]], ht2[:, [2, 0]]])
S = ac.copy()
deg = np.zeros(len(ac)); np.add.at(deg, E2[:, 0], 1); np.add.at(deg, E2[:, 1], 1)
for _ in range(int(os.environ.get('CHIN_PASSES', '12'))):
    acc = np.zeros_like(S); np.add.at(acc, E2[:, 0], S[E2[:, 1]]); np.add.at(acc, E2[:, 1], S[E2[:, 0]])
    nb = acc / np.maximum(deg, 1)[:, None]; S = S + (nb - S) * (0.5 * cw)[:, None]
S[:, 0] = np.where(np.abs(ac[:, 0]) < 1e-6, 0.0, S[:, 0])
delta += (S - ac)
co += delta[D['orig']]
print('TWEAK hairline taper', TAPER, int((w > 0.05).sum()), 'verts; chin smoothed', int((cw > 0.05).sum()), 'verts, max move', round(float(np.abs(S - ac).max()) * 1000, 1), 'mm')
# neck seam (user review r15: a line across the neck): the head's neck tube and the dress's neckline meet at a crease on the level seam;
# positions of head and dress within 2.5 cm of the seam are Laplacian-smoothed together (welded by position, so the seam stays closed)
dp = [str(x) for x in A['names']].index('dress')
mskp = np.isin(acomp, [hk, dp]) & ~eyev & (np.abs(ac[:, 2] - 0.5703) < 0.014) & ~((acomp == hk) & (ac[:, 1] < -0.04) & (ac[:, 2] > 0.574))   # not the chin
from scipy.sparse.csgraph import connected_components as _cc
from scipy.sparse import coo_matrix as _coo
_pairs = cKDTree(ac).query_pairs(2e-4, output_type='ndarray')          # weld head / dress copies of the seam vertices (rounding split some)
_g = _coo((np.ones(len(_pairs)), (_pairs[:, 0], _pairs[:, 1])), shape=(len(ac), len(ac)))
nw, wid = _cc(_g, directed=False)
tp = at[np.isin(acomp[at[:, 0]], [hk, dp])]; Ew = np.unique(np.sort(np.vstack([wid[tp[:, [0, 1]]], wid[tp[:, [1, 2]]], wid[tp[:, [2, 0]]]]), 1), axis=0)
Pw = np.zeros((nw, 3)); np.add.at(Pw, wid, ac); Pw /= np.bincount(wid, minlength=nw)[:, None]; Q = Pw.copy()
ww = np.zeros(nw); ww[wid[mskp]] = (1 - ss(np.abs(ac[mskp, 2] - 0.5703), 0.005, 0.014))
dg = np.zeros(nw); np.add.at(dg, Ew[:, 0], 1); np.add.at(dg, Ew[:, 1], 1)
_ea = np.sort(np.vstack([wid[tp[:, [0, 1]]], wid[tp[:, [1, 2]]], wid[tp[:, [2, 0]]]]), 1); _ue, _ce = np.unique(_ea, axis=0, return_counts=True)
ww[np.unique(_ue[_ce == 1].ravel())] = 0.0                 # open rims (the dress neckline, the hair edge) stay where they are
for _ in range(int(os.environ.get('SEAM_PASSES', '8'))):
    acc = np.zeros_like(Q); np.add.at(acc, Ew[:, 0], Q[Ew[:, 1]]); np.add.at(acc, Ew[:, 1], Q[Ew[:, 0]])
    Q = Q + (acc / np.maximum(dg, 1)[:, None] - Q) * (0.5 * ww)[:, None]
Q[np.abs(Pw[:, 0]) < 1e-6, 0] = 0.0
_m = np.linalg.norm(Q - Pw, axis=1, keepdims=True); Q = Pw + (Q - Pw) * np.minimum(1, 0.003 / np.maximum(_m, 1e-9))
dlt = (Q[wid] - ac) * (ww[wid] > 0)[:, None] + (Q - Pw)[wid] * (ww[wid] <= 0)[:, None]; co += dlt[D['orig']]
print('TWEAK neck seam smoothed', int((ww > 0.05).sum()), 'welded verts, max move', round(float(np.abs(Q - Pw).max()) * 1000, 1), 'mm')
# nose (user review r15/r16: brown blotches round the nostrils and a dark streak down the side of the nose in the lit viewer = the
# geometry: Meshy's nostril cavities and faceted alae shade dark): head vertices of the nose Laplacian-smoothed in place (welded head graph,
# 10 passes, feathered, at most 2.5 mm), positions only
nw_ = (1 - ss(np.abs(ac[:, 0]), 0.016, 0.024)) * ss(ac[:, 2], 0.636, 0.642)      # above the upper lip (0.633) * (1 - ss(ac[:, 2], 0.665, 0.675)) * (ac[:, 1] < -0.095)
nw_[~((acomp == hk) & ~eyev)] = 0
Sn = ac.copy()
for _ in range(int(os.environ.get('NOSE_PASSES', '0'))):     # off: the capped smoothing left lumpy alae in the viewer (r19); 0 keeps Meshy's nose
    acc = np.zeros_like(Sn); np.add.at(acc, E2[:, 0], Sn[E2[:, 1]]); np.add.at(acc, E2[:, 1], Sn[E2[:, 0]])
    Sn = Sn + (acc / np.maximum(deg, 1)[:, None] - Sn) * (0.5 * nw_)[:, None]
Sn[np.abs(ac[:, 0]) < 1e-6, 0] = 0.0
_mn = np.linalg.norm(Sn - ac, axis=1, keepdims=True); Sn = ac + (Sn - ac) * np.minimum(1, 0.0025 / np.maximum(_mn, 1e-9))
co += (Sn - ac)[D['orig']]
print('TWEAK nose smoothed', int((nw_ > 0.05).sum()), 'verts, max move', round(float(_mn.max()) * 1000, 1), 'mm (capped 2.5)')
# bridge (coordinator review r20: a dark diamond at the top of the bridge): Meshy's micro-facets on the midline between the brows
# (18 vertex pairs closer than 0.5 mm) smoothed, at most 1 mm, positions only
bw2 = (1 - ss(np.abs(ac[:, 0]), 0.010, 0.018)) * ss(ac[:, 2], 0.668, 0.676) * (1 - ss(ac[:, 2], 0.705, 0.715)) * (ac[:, 1] < -0.09)
bw2[~((acomp == hk) & ~eyev)] = 0
Sb = ac.copy()
for _ in range(6):
    acc = np.zeros_like(Sb); np.add.at(acc, E2[:, 0], Sb[E2[:, 1]]); np.add.at(acc, E2[:, 1], Sb[E2[:, 0]])
    Sb = Sb + (acc / np.maximum(deg, 1)[:, None] - Sb) * (0.5 * bw2)[:, None]
Sb[np.abs(ac[:, 0]) < 1e-6, 0] = 0.0
_mb = np.linalg.norm(Sb - ac, axis=1, keepdims=True); Sb = ac + (Sb - ac) * np.minimum(1, 0.001 / np.maximum(_mb, 1e-9))
co += (Sb - ac)[D['orig']]
print('TWEAK bridge smoothed', int((bw2 > 0.05).sum()), 'verts')
# midline crease (coordinator review r23: a light vertical line down the lips and chin; the clay render shows a V crease at x = 0 where the
# mirrored halves meet at an angle): head vertices within 1 cm of the midline on the lower face are smoothed in depth only (x kept, so the
# halves stay mirrored; z-smoothing notched the chin), 8 passes, at most 1.2 mm
mw2 = (1 - ss(np.abs(ac[:, 0]), 0.003, 0.010)) * ss(ac[:, 2], 0.5706, 0.574) * (1 - ss(ac[:, 2], 0.770, 0.785))   # r25: up the forehead too (stitch-like midline) * (ac[:, 1] < -0.045)   # down the neck to the seam (a fin under the chin)
mw2[~((acomp == hk) & ~eyev)] = 0
Sm = ac.copy()
for _ in range(8):
    acc = np.zeros_like(Sm); np.add.at(acc, E2[:, 0], Sm[E2[:, 1]]); np.add.at(acc, E2[:, 1], Sm[E2[:, 0]])
    nb = acc / np.maximum(deg, 1)[:, None]; Sm[:, 1] = Sm[:, 1] + (nb[:, 1] - Sm[:, 1]) * (0.5 * mw2)
_mm = np.linalg.norm(Sm - ac, axis=1, keepdims=True); Sm = ac + (Sm - ac) * np.minimum(1, 0.002 / np.maximum(_mm, 1e-9))
co += (Sm - ac)[D['orig']]; D['co'] = co
print('TWEAK midline crease smoothed', int((mw2 > 0.05).sum()), 'verts')
# a folded triangle pair under the chin on the midline (two midline vertices stacked 2.3 mm apart at the chin-neck fold; one face points up:
# a light wedge from below): the fold's vertices are smoothed in all axes, 10 passes, at most 1.5 mm
fw = (1 - ss(np.abs(ac[:, 0]), 0.003, 0.007)) * (1 - ss(np.abs(ac[:, 2] - 0.587), 0.004, 0.007)) * (1 - ss(np.abs(ac[:, 1] + 0.074), 0.006, 0.010))
fw[~((acomp == hk) & ~eyev)] = 0
Sf = ac.copy()
for _ in range(10):
    acc = np.zeros_like(Sf); np.add.at(acc, E2[:, 0], Sf[E2[:, 1]]); np.add.at(acc, E2[:, 1], Sf[E2[:, 0]])
    Sf = Sf + (acc / np.maximum(deg, 1)[:, None] - Sf) * (0.5 * fw)[:, None]
Sf[np.abs(ac[:, 0]) < 1e-6, 0] = 0.0
_mf = np.linalg.norm(Sf - ac, axis=1, keepdims=True); Sf = ac + (Sf - ac) * np.minimum(1, 0.0015 / np.maximum(_mf, 1e-9))
co += (Sf - ac)[D['orig']]; D['co'] = co
# then any head face on the lower face still folded against its neighbours (normal opposite to their mean) has its shortest edge collapsed
_cur = ac + (co[np.argsort(D['orig'])][:0].sum() if False else 0)
_P = ac.copy(); _P[D['orig']] = co            # current positions per asm vertex
_ht = at[acomp[at[:, 0]] == hk]; _n = np.cross(_P[_ht[:, 1]] - _P[_ht[:, 0]], _P[_ht[:, 2]] - _P[_ht[:, 0]]); _n /= np.maximum(np.linalg.norm(_n, axis=1, keepdims=True), 1e-12)
_vn = np.zeros_like(_P)
for k in range(3): np.add.at(_vn, _ht[:, k], _n)
_nb = _vn[_ht].sum(1) - 3 * _n; _nb /= np.maximum(np.linalg.norm(_nb, axis=1, keepdims=True), 1e-12)
_cen = _P[_ht].mean(1)
_bad = np.where(((_n * _nb).sum(1) < -0.2) & (_cen[:, 2] > 0.57) & (_cen[:, 2] < 0.62) & (_cen[:, 1] < -0.04) & (np.abs(_cen[:, 0]) < 0.02))[0]
_mv = {}
for f in _bad:
    t_ = _ht[f]; L_ = [np.linalg.norm(_P[t_[i]] - _P[t_[(i + 1) % 3]]) for i in range(3)]; i = int(np.argmin(L_)); a_, b_ = t_[i], t_[(i + 1) % 3]
    m_ = 0.5 * (_P[a_] + _P[b_]); _mv[a_] = m_; _mv[b_] = m_
for v_, m_ in _mv.items():
    sel_ = D['orig'] == v_; co[sel_] = m_
# ear-root stubs (coordinator review r24: small dark specks beside the jaw in front views = a few crumpled head-shell triangles of the ear
# root poking out sideways between the face edge and the hair): the shell behind the jaw's front edge, at ear height, is drawn in toward
# 6.3 cm off the midline so the hair covers it (the elf ear part is separate and keeps its place)
_ax = np.abs(co[:, 0])
_ew = sv * ss(co[:, 2], 0.628, 0.638) * (1 - ss(co[:, 2], 0.682, 0.692)) * ss(co[:, 1], -0.054, -0.046) * (co[:, 1] < 0.01) * (_ax > 0.063)
co[:, 0] = np.where(_ew > 0, np.sign(co[:, 0]) * (0.063 + (_ax - 0.063) * (1 - 0.85 * _ew)), co[:, 0])
print('TWEAK ear-root stubs drawn in', int((_ew > 0.05).sum()), 'verts')
# relaxed mouth (user review r25, "whats wrong with the mouth?": a tight forward bud with dark wedge corners; like the approved boys'
# lip_sculpt.py): the mouth patch's front surface (|x| < 3.4 cm, 2.6 cm about the lip line LIP_Z) is replaced by a smooth base, a
# bilaplacian fill from the face round it (the muzzle's curvature carries on, no bud, no corner notches, no chin dimple), plus subtle
# lips sculpted into it: upper +0.8 mm, lower +1.2 mm, a 0.3 mm groove on the line, a 0.5 mm mentolabial dip, a faint philtrum, the
# corners tucked 0.6 mm. Depth (y) only; the mouth's inner faces behind the front follow their nearest front vertex.
import scipy.sparse as _sp, scipy.sparse.linalg as _spl
LZ = float(os.environ.get('LIP_Z', '0.6272')); HALF = 0.021
_P = ac.copy(); _P[D['orig']] = co
_sh = np.where(shell)[0]
_E = E2[shell[E2[:, 0]] & shell[E2[:, 1]]]
# front surface: within 4 mm of the front-most shell point in a 2.5 mm (x, z) neighbourhood
_box = shell & (np.abs(_P[:, 0]) < 0.050) & (np.abs(_P[:, 2] - LZ) < 0.040) & (_P[:, 1] < -0.04)
_bi = np.where(_box)[0]; _kd = cKDTree(_P[_bi][:, [0, 2]])
_ymin = np.array([_P[_bi][j, 1].min() for j in _kd.query_ball_point(_P[_bi][:, [0, 2]], 0.0025)])
_front = np.zeros(len(ac), bool); _front[_bi] = _P[_bi, 1] - _ymin < 0.004
_dz = _P[:, 2] - LZ; _ax = np.abs(_P[:, 0])
_fade = np.clip(np.minimum(np.minimum((0.031 - _ax) / 0.008, (_dz + 0.026) / 0.010), (0.0135 - _dz) / 0.005), 0, 1)   # under the nose
_free = _front & (_fade > 0)
_fix = _front & ~_free
_n = len(ac)
# smooth base: a low-order surface y = f(x^2, z) fitted to the front of the whole box (the face round the mouth anchors it)
def _basis(x, z):
    x2 = (x / 0.03) ** 2; zz = z / 0.02
    return np.stack([np.ones_like(x), zz, zz ** 2, zz ** 3, zz ** 4, x2, x2 * zz, x2 * zz ** 2, x2 ** 2, x2 ** 2 * zz, x2 ** 3], 1)
_fb = np.where(_front & (np.abs(_P[:, 0]) < 0.038) & (_dz > -0.036) & (_dz < 0.016))[0]
_coef, *_ = np.linalg.lstsq(_basis(_P[_fb, 0], _dz[_fb]), _P[_fb, 1], rcond=None)
_fi = np.where(_free)[0]
_yb = _basis(_P[_fi, 0], _dz[_fi]) @ _coef
_res = _P[_fb, 1] - _basis(_P[_fb, 0], _dz[_fb]) @ _coef
print('LIP base fit residual mm: rms', round(float(np.sqrt((_res ** 2).mean())) * 1000, 2), 'max', round(float(np.abs(_res).max()) * 1000, 2))
_g = lambda x, s_: np.exp(-(x / s_) ** 2)
_u = _ax[_fi] / HALF; _t = np.clip(1 - _u * _u, 0, 1); _z = _dz[_fi]
_d = 0.0008 * _t ** 0.7 * _g(_z - 0.0022, 0.0018) + 0.0012 * _t ** 0.7 * _g(_z + 0.0030, 0.0024) - 0.0003 * _t * _g(_z, 0.0006) \
    - 0.0005 * _t * _g(_z + 0.0085, 0.0022) - 0.0006 * _g(_u - 1.0, 0.18) * _g(_z, 0.004)
_ph = (_ax[_fi] < 0.004) & (_z > 0.004) & (_z < 0.012)
_d -= np.where(_ph, 0.0003 * (1 - _ax[_fi] / 0.004) * np.sin(np.pi * np.clip((_z - 0.004) / 0.008, 0, 1)), 0)
_ynew = _P[_fi, 1] + ((_yb - _d) - _P[_fi, 1]) * _fade[_fi]
_dy = np.zeros(_n); _dy[_fi] = _ynew - _P[_fi, 1]
# inner faces (the slit's lips, the mouth cavity) behind the front follow the nearest front vertex, fading out 1.5 cm behind it
_in = shell & ~_front & (np.abs(_P[:, 0]) < 0.040) & (np.abs(_dz) < 0.030)
_ii = np.where(_in)[0]
if len(_ii):
    _kf = cKDTree(_P[_fi][:, [0, 2]]); _dd, _jj = _kf.query(_P[_ii][:, [0, 2]])
    _beh = _P[_ii, 1] - _P[_fi][_jj, 1]
    _dy[_ii] = _dy[_fi][_jj] * np.clip(1 - _beh / 0.015, 0, 1) * (_dd < 0.004)
co[:, 1] += _dy[D['orig']]
# r27 (coordinator: finalise the mouth before a fresh paint): the lips' edges along the slit zig-zag (upper 0.6277-0.6307, lower
# 0.6245-0.6268) and the slit ends in a notch at each corner. The edges now follow one smooth symmetric curve (a closed line rising
# 1 mm to the corners), 0.3 mm either side of it, closing to nothing at the corners; the rows beside them are relaxed in height; the
# slit's pocket (inner vertices within 8 mm behind the front) is drawn onto the line just behind the edges, fully at the corners, so the
# corners flow into the cheeks. Positions only.
_P2 = _P.copy(); _P2[:, 1] += _dy
_zone = shell & (np.abs(_P[:, 0]) < 0.026) & (np.abs(_dz) < 0.007)
_inm = _zone & ~_front
_nbin = np.zeros(len(ac), bool); np.logical_or.at(_nbin, _E[:, 0], _inm[_E[:, 1]]); np.logical_or.at(_nbin, _E[:, 1], _inm[_E[:, 0]])
_edge = _zone & _front & _nbin & (np.abs(_P[:, 0]) < 0.0215)
# upper / lower edge: where the front neighbours (not on the edge) lie
_sz = np.zeros(len(ac)); _sn = np.zeros(len(ac)); _fne = _front & ~_edge
np.add.at(_sz, _E[:, 0], np.where(_fne[_E[:, 1]], _P2[_E[:, 1], 2], 0)); np.add.at(_sn, _E[:, 0], _fne[_E[:, 1]])
np.add.at(_sz, _E[:, 1], np.where(_fne[_E[:, 0]], _P2[_E[:, 0], 2], 0)); np.add.at(_sn, _E[:, 1], _fne[_E[:, 0]])
_up = _edge & (_sz / np.maximum(_sn, 1) > _P2[:, 2])
_ax2 = np.abs(_P2[:, 0])
LZC = 0.6270; _zc = LZC + 0.0014 * (np.clip(_ax2, 0, 0.020) / 0.020) ** 2
_gap = 0.0003 * (1 - ss(_ax2, 0.012, 0.019))
_grv = 0.0004 * (1 - ss(_ax2, 0.010, 0.019))
# the front surface's depth without the slit: the same low-order fit, on the front away from the edges
_fs = np.where(_front & ~_edge & (np.abs(_P2[:, 0]) < 0.034) & (np.abs(_P2[:, 2] - LZ) < 0.020) & ~(np.abs(_P2[:, 2] - LZ) < 0.0025))[0]
_c2, *_ = np.linalg.lstsq(_basis(_P2[_fs, 0], _P2[_fs, 2] - LZ), _P2[_fs, 1], rcond=None)
_ys = lambda x, z: _basis(x, z - LZ) @ _c2
_ei = np.where(_edge)[0]
_tz = _zc[_ei] + np.where(_up[_ei], 1, -1) * _gap[_ei]
_ty = _ys(_P2[_ei, 0], _tz) + _grv[_ei]
_new = _P2.copy(); _new[_ei, 2] = _tz; _new[_ei, 1] = np.minimum(_ty, _P2[_ei, 1] + 0.0015)   # never pulled back more than 1.5 mm
# pocket onto the line, just behind the edges (fully at the corners)
_pi = np.where(_inm & (np.abs(_P2[:, 0]) < 0.024))[0]
if len(_pi):
    _kf2 = cKDTree(_P2[_fi][:, [0, 2]]); _d2, _j2 = _kf2.query(_P2[_pi][:, [0, 2]])
    _bh = _P2[_pi, 1] - _P2[_fi][_j2, 1]
    _pk = _bh < 0.008
    _pi = _pi[_pk]
    _new[_pi, 2] = _zc[_pi]
    _new[_pi, 1] = _ys(_P2[_pi, 0], _zc[_pi]) + _grv[_pi] + 0.0003
# the rows beside the edges: height relaxed toward their neighbours (edges and pocket fixed), feathered 6 mm from the line
_fixd = np.zeros(len(ac), bool); _fixd[_ei] = True; _fixd[_pi] = True
_rw = _front & ~_fixd & (np.abs(_P2[:, 0]) < 0.026) & (np.abs(_P2[:, 2] - LZC) < 0.007)
_rwt = (1 - ss(np.abs(_P2[:, 2] - LZC), 0.003, 0.007)) * (1 - ss(np.abs(_P2[:, 0]), 0.019, 0.026)) * _rw
for _ in range(6):
    _acc = np.zeros(len(ac)); _cn = np.zeros(len(ac))
    np.add.at(_acc, _E[:, 0], _new[_E[:, 1], 2]); np.add.at(_cn, _E[:, 0], 1); np.add.at(_acc, _E[:, 1], _new[_E[:, 0], 2]); np.add.at(_cn, _E[:, 1], 1)
    _new[:, 2] = np.where(_rwt > 0, _new[:, 2] + (_acc / np.maximum(_cn, 1) - _new[:, 2]) * 0.5 * _rwt, _new[:, 2])
# and in depth within 4 mm of the line (the midline's micro-facets stood 1 mm proud of the edges: a light dot; a ledge at the corners)
_rwy = _front & ~_fixd & (np.abs(_P2[:, 0]) < 0.026) & (np.abs(_P2[:, 2] - LZC) < 0.004)
_rwyt = (1 - ss(np.abs(_P2[:, 2] - LZC), 0.0015, 0.004)) * (1 - ss(np.abs(_P2[:, 0]), 0.019, 0.026)) * _rwy
for _ in range(8):
    _acc = np.zeros(len(ac)); _cn = np.zeros(len(ac))
    np.add.at(_acc, _E[:, 0], _new[_E[:, 1], 1]); np.add.at(_cn, _E[:, 0], 1); np.add.at(_acc, _E[:, 1], _new[_E[:, 0], 1]); np.add.at(_cn, _E[:, 1], 1)
    _new[:, 1] = np.where(_rwyt > 0, _new[:, 1] + (_acc / np.maximum(_cn, 1) - _new[:, 1]) * 0.5 * _rwyt, _new[:, 1])
_new[np.abs(ac[:, 0]) < 1e-6, 0] = 0.0
_mv = _new - _P2
co += _mv[D['orig']]
print('TWEAK slit: edges', len(_ei), '(upper', int(_up.sum()), ') pocket', len(_pi), 'max move', round(float(np.abs(_mv).max()) * 1000, 1), 'mm')
if os.environ.get('LIP_DEBUG'):
    _o = np.argsort(_dy[_fi])
    for k in list(_o[:6]) + list(_o[-6:]): print('  dy', round(_dy[_fi][k] * 1000, 1), _P[_fi][k].round(4), 'yb', round(_yb[k], 4), 'fade', round(_fade[_fi][k], 2))
print('TWEAK mouth relaxed: front', int(_free.sum()), 'verts, inner', len(_ii), ', depth change', round(float(_dy.min()) * 1000, 1), '..',
      round(float(_dy.max()) * 1000, 1), 'mm')
D['co'] = co
print('TWEAK chin fold smoothed', int((fw > 0.05).sum()), 'verts; folded faces collapsed', len(_bad))
print('TWEAK lower lids up', LID, n_lid, 'verts')
np.savez(OUT, **D); print('TWEAK eyes forward', FWD, int(sel.sum()), 'verts')
