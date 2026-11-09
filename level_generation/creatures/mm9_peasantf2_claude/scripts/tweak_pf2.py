#!/usr/bin/env python3
"""PF2 (copy of mm9_peasantf7_claude/scripts/tweak_pf7.py with F2 landmarks; from mm9_peasantf5_claude/scripts/tweak_pf.py, F7 landmarks; the hand-stub step dropped: F7 has one MPFB arm+hand). Geometry tweaks after the paint (UVs unchanged, the paint moves with the mesh): the mirrored head meets itself at x = 0 at an angle, a crease
that shaded as a dark line down the chin and a light strip on the nose. Vertices within BAND of the midline on the face are pulled forward
(depth only, valleys only, at most 3 mm), so the halves meet smoothly; ridges (the nose) are left. Args: <asm npz> <uv_tex npz> <out npz> [band m] [passes]"""
import sys
import numpy as np
A, U, OUT = sys.argv[1:4]; CAP = 0.003; BAND = float(sys.argv[4]) if len(sys.argv) > 4 else 0.010; PASSES = int(sys.argv[5]) if len(sys.argv) > 5 else int(__import__('os').environ.get('MID_PASSES', '8'))
S = np.load(A); co, tri, comp = S['co'].copy(), S['tri'], S['comp']; names = [str(x) for x in S['names']]
D = dict(np.load(U))
for part in ('head',):
    k = names.index(part); t = tri[comp[tri[:, 0]] == k]
    e = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    sel = (comp == k) & (np.abs(co[:, 0]) < BAND) & (co[:, 1] < -0.05)
    mid = (comp == k) & (np.abs(co[:, 0]) < 1e-5)
    w = np.clip(1 - np.abs(co[:, 0]) / BAND, 0, 1)[:, None]
    P = co.copy()
    for _ in range(PASSES):
        acc = np.zeros_like(P); deg = np.zeros(len(P))
        np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        L = acc / np.maximum(deg, 1)[:, None]
        dP = (L - P) * 0.5 * w
        dP[:, 0] = 0; dP[:, 2] = 0                                  # depth only, and only where the midline is a valley (moves forward, -y)
        dP[:, 1] = np.minimum(dP[:, 1], 0)
        P[sel] = P[sel] + dP[sel]
        P[sel] = co[sel] + np.clip(P[sel] - co[sel], -CAP, CAP)
        P[mid, 0] = 0
    d = np.linalg.norm(P - co, axis=1); print('TWEAK', part, 'moved', int((d > 1e-5).sum()), 'max mm', round(float(d.max()) * 1000, 2))
    co = P
# slivers: the bisect left vertices a hair off the plane (|x| 0.2-2 mm) whose mirror twins make needle faces with steep normals along the
# midline (the dark line down the chin). Snapped onto x = 0 they become zero-area faces that add nothing to the normals.
SNAP = float(__import__('os').environ.get('SNAP', '0.0025'))
for part in ('head', 'dress', 'skirt'):
    k = names.index(part); q = (comp == k) & (np.abs(co[:, 0]) < SNAP) & (np.abs(co[:, 0]) > 0)
    co[q, 0] = 0; print('SNAP', part, int(q.sum()))
# mouth (orchestrator review 2026-11-02: a protruding pout, lips pushed forward into a bulb): the lips' front surface is compared with a
# heavily smoothed copy of it (nose and chin outside the box hold it), and every vertex of the mouth column (lips and the cavity behind them)
# moves back by the lips' excess at its (x, z), feathered at the box edge, at most 6 mm: the lips go back onto the face without folding the
# cavity through them. Positions only (UVs and weights unchanged).
import os as _os
from scipy.spatial import cKDTree as _KD
MZ0, MZ1, MX = 0.607, 0.640, 0.034
kh_ = names.index('head'); th_ = tri[comp[tri[:, 0]] == kh_]
eh_ = np.unique(np.sort(np.vstack([th_[:, [0, 1]], th_[:, [1, 2]], th_[:, [2, 0]]]), axis=1), axis=0)
def _ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
col = (comp == kh_) & (np.abs(co[:, 0]) < MX + 0.008) & (co[:, 2] > MZ0 - 0.010) & (co[:, 2] < MZ1 + 0.008) & (co[:, 1] < -0.03)
ci = np.where(col)[0]; Pc = co[ci]
front = np.zeros(len(ci), bool)
for i_ in range(len(ci)):
    d_ = np.hypot(Pc[:, 0] - Pc[i_, 0], Pc[:, 2] - Pc[i_, 2]); front[i_] = Pc[i_, 1] - Pc[d_ < 0.003, 1].min() < 0.0015
fv = ci[front]
wgt = _ss(MX - np.abs(co[:, 0]), 0.0, 0.010) * _ss(co[:, 2] - MZ0, 0.0, 0.010) * _ss(MZ1 - co[:, 2], 0.0, 0.006)
isf = np.zeros(len(co), bool); isf[fv] = True
reg = isf & (wgt > 0)
dg_ = np.zeros(len(co)); np.add.at(dg_, eh_[:, 0], 1); np.add.at(dg_, eh_[:, 1], 1)
S_ = co.copy()
for _ in range(int(_os.environ.get('MOUTH_PASSES', '80'))):
    acc = np.zeros_like(S_); np.add.at(acc, eh_[:, 0], S_[eh_[:, 1]]); np.add.at(acc, eh_[:, 1], S_[eh_[:, 0]])
    L_ = acc / np.maximum(dg_, 1)[:, None]; S_[reg, 1] = S_[reg, 1] + 0.5 * (L_[reg, 1] - S_[reg, 1])
K_ = float(_os.environ.get('MOUTH_K', '0.8'))
exc = np.clip(S_[fv, 1] - co[fv, 1], 0, 0.006) * K_ * wgt[fv]           # how far each front vertex stands out of the smoothed face
kd_ = _KD(co[fv][:, [0, 2]]); dd_, nn_ = kd_.query(co[ci][:, [0, 2]], k=4); ww_ = 1 / np.maximum(dd_, 1e-4)
dy = (exc[nn_] * ww_).sum(1) / ww_.sum(1) * (wgt[ci] > 0)
co[ci, 1] += dy
print('MOUTH front verts', len(fv), 'moved back', int((dy > 1e-4).sum()), 'max mm', round(float(dy.max()) * 1000, 2))
# eye creases and nostrils (orchestrator review 2026-11-02: lit from above, Meshy's deep lid crease under the brow and the open nostril holes
# drew a dark band over each eye and a dark triangle under the nose): the crease band above each eye (eyeball excluded) and the nose's
# underside are Laplacian-smoothed in place, at most 3.5 mm. Positions only.
def _smooth(mask, passes, cap):
    global co
    c0_ = co.copy(); S2 = co.copy()
    for _ in range(passes):
        acc = np.zeros_like(S2); np.add.at(acc, eh_[:, 0], S2[eh_[:, 1]]); np.add.at(acc, eh_[:, 1], S2[eh_[:, 0]])
        L2 = acc / np.maximum(dg_, 1)[:, None]; S2[mask] = S2[mask] + 0.5 * (L2[mask] - S2[mask])
    d2 = S2 - c0_; n2 = np.linalg.norm(d2, axis=1, keepdims=True); co = c0_ + d2 * np.minimum(1, cap / np.maximum(n2, 1e-9))
    co[mask & (np.abs(c0_[:, 0]) < 1e-6), 0] = 0
    return float(np.linalg.norm(co - c0_, axis=1).max())
_hv = np.where(comp == kh_)[0]; _par = np.arange(len(co))
def _g(q):
    while _par[q] != q: _par[q] = _par[_par[q]]; q = _par[q]
    return q
for a_, b_, c_ in th_:
    r_ = _g(a_); _par[_g(b_)] = r_; _par[_g(c_)] = r_
_rt = np.array([_g(v) for v in _hv]); _big = np.bincount(_rt).argmax(); _eye = np.zeros(len(co), bool); _eye[_hv[_rt != _big]] = True
EC = 0.688; EX = 0.0275
crease = (comp == kh_) & ~_eye & (np.abs(np.abs(co[:, 0]) - EX) < 0.024) & (co[:, 2] > EC + 0.004) & (co[:, 2] < EC + 0.024) & (co[:, 1] < -0.055)
print('EYE CREASE smoothed', int(crease.sum()), 'verts, max mm', round(_smooth(crease, int(_os.environ.get('CREASE_PASSES', '0')), 0.0035) * 1000, 2))
nost = (comp == kh_) & (np.abs(co[:, 0]) > 0.003) & (np.abs(co[:, 0]) < 0.020) & (co[:, 2] > 0.6335) & (co[:, 2] < 0.6505) & (co[:, 1] < -0.077) & (co[:, 1] > -0.1145)
print('NOSTRILS smoothed', int(nost.sum()), 'verts, max mm', round(_smooth(nost, int(_os.environ.get('NOSE_PASSES', '8')), 0.002) * 1000, 2))
# ---- nose fix 2026-11-02 (user: "something wrong on her nose?"; the same faults as PeasantF1, after mm9_peasantf1_claude/scripts/tweak_pf1.py)
from scipy.sparse import coo_matrix as _coo
from scipy.sparse.linalg import spsolve as _spsolve
from scipy.ndimage import grey_erosion as _ge
Z0_ = -0.9297
_ku = np.round(co, 5); _uu, _iu = np.unique(_ku, axis=0, return_inverse=True); _iu = _iu.ravel(); NU = len(_uu)
_th = _iu[th_[~_eye[th_].any(1)]]
_E = np.unique(np.sort(np.vstack([_th[:, [0, 1]], _th[:, [1, 2]], _th[:, [2, 0]]]), axis=1), axis=0); _E = _E[_E[:, 0] != _E[:, 1]]
_adj = [[] for _ in range(NU)]
for a_, b_ in _E: _adj[a_].append(b_); _adj[b_].append(a_)
_deg = np.bincount(_E.ravel(), minlength=NU).astype(float)
# (1) the mouth: the lips were moved back onto the face but the slit still opened into Meshy's cavity, whose inner lips faced up and down
# between them: a lighter band inside the lips (a second lip layer) and a puckered "O" from below. Closed as one unfolded surface: the
# cavity's positions (more than 2 mm behind the local front, plus the hidden sack behind them) spread over the opening by a Tutte embedding
# in (x, z), the depth a harmonic fill of the rim's plus a dome (MOUTH_DOME) and a shallow groove (MOUTH_GROOVE) on the repaint's lip line
# (MOUTH_SLIT, m over the soles).
LZ = float(_os.environ.get('MOUTH_SLIT', '1.5542')) + Z0_
_hp = np.where(~_eye & (comp == kh_) & (np.abs(co[:, 0]) < 0.03) & (np.abs(co[:, 2] - LZ) < 0.016) & (co[:, 1] < -0.04))[0]
_P2 = co[_hp]; _cav = np.zeros(len(co), bool)
for i_ in range(len(_hp)):
    d_ = np.hypot(_P2[:, 0] - _P2[i_, 0], _P2[:, 2] - _P2[i_, 2])
    if _P2[i_, 1] - _P2[d_ < 0.0035, 1].min() > 0.002: _cav[_hp[i_]] = True
free = np.zeros(NU, bool); free[_iu[_cav]] = True
_RES = 0.00025; _X0 = -0.05; _ZL = LZ - 0.045; _NX = int(0.1 / _RES); _NZ = int(0.09 / _RES); _Zb = np.full((_NZ, _NX), 1.0)
for _t in _th:
    _q = _uu[_t]; _gx = (_q[:, 0] - _X0) / _RES; _gz = (_q[:, 2] - _ZL) / _RES
    _x0, _x1 = int(max(np.floor(_gx.min()), 0)), int(min(np.ceil(_gx.max()), _NX - 1)); _z0, _z1 = int(max(np.floor(_gz.min()), 0)), int(min(np.ceil(_gz.max()), _NZ - 1))
    if _x1 < _x0 or _z1 < _z0: continue
    _X, _Zg = np.meshgrid(np.arange(_x0, _x1 + 1), np.arange(_z0, _z1 + 1))
    _d = (_gz[1] - _gz[2]) * (_gx[0] - _gx[2]) + (_gx[2] - _gx[1]) * (_gz[0] - _gz[2])
    if abs(_d) < 1e-12: continue
    _a = ((_gz[1] - _gz[2]) * (_X - _gx[2]) + (_gx[2] - _gx[1]) * (_Zg - _gz[2])) / _d; _b = ((_gz[2] - _gz[0]) * (_X - _gx[2]) + (_gx[0] - _gx[2]) * (_Zg - _gz[2])) / _d
    _m = (_a >= -1e-6) & (_b >= -1e-6) & (1 - _a - _b >= -1e-6); _yy = _a * _q[0, 1] + _b * _q[1, 1] + (1 - _a - _b) * _q[2, 1]
    _sub = _Zb[_z0:_z1 + 1, _x0:_x1 + 1]; _up = _m & (_yy < _sub); _sub[_up] = _yy[_up]
_Zb = _ge(_Zb, size=3)
_ix = np.clip(np.round((_uu[:, 0] - _X0) / _RES).astype(int), 0, _NX - 1); _iz = np.clip(np.round((_uu[:, 2] - _ZL) / _RES).astype(int), 0, _NZ - 1)
hidden = (np.abs(_uu[:, 0]) < 0.045) & (np.abs(_uu[:, 2] - LZ) < 0.04) & (_uu[:, 1] - _Zb[_iz, _ix] > 0.0015)
_st = list(np.where(free)[0])
while _st:
    _v = _st.pop()
    for _w in _adj[_v]:
        if hidden[_w] and not free[_w]: free[_w] = True; _st.append(_w)
if _os.environ.get('MOUTH_CLOSE', '1') != '1': free[:] = False      # PF7: Meshy's slit is nearly closed; the unfold puffed the lips (r3)
fi_ = np.where(free)[0]; loc = -np.ones(NU, int); loc[fi_] = np.arange(len(fi_))
r_, c_, v_ = [], [], []; rhs = np.zeros((len(fi_), 3)); rim = np.zeros(NU, bool)
for a_, b_ in _E:
    for p_, q_ in ((a_, b_), (b_, a_)):
        if not free[p_]: continue
        if free[q_]: r_.append(loc[p_]); c_.append(loc[q_]); v_.append(-1.0)
        else: rhs[loc[p_]] += _uu[q_]; rim[q_] = True
r_ += list(range(len(fi_))); c_ += list(range(len(fi_))); v_ += list(_deg[fi_])
Lm = _coo((v_, (r_, c_)), shape=(len(fi_), len(fi_))).tocsr()
sol = np.stack([_spsolve(Lm, rhs[:, k]) for k in range(3)], -1) if len(fi_) else np.zeros((0, 3))
phi = _spsolve(Lm, np.ones(len(fi_))) if len(fi_) else np.zeros(0); phi = phi / max(phi.max() if len(phi) else 1, 1e-12)
DOME = float(_os.environ.get('MOUTH_DOME', '0.0007')); GROOVE = float(_os.environ.get('MOUTH_GROOVE', '0.0004'))
newp = sol.copy(); newp[:, 1] = sol[:, 1] - DOME * np.sqrt(phi)
zsl = LZ + 4.0 * newp[:, 0] ** 2
newp[:, 1] += GROOVE * np.exp(-((newp[:, 2] - zsl) / 0.0009) ** 2) * np.clip(1 - np.abs(newp[:, 0]) / 0.024, 0, 1)
_uu[fi_] = newp; _mv = free[_iu]; co[_mv] = _uu[_iu[_mv]]
print('MOUTH closed (unfolded): cavity positions', len(fi_))
# (2) the nose tip and underside: a facet 9 mm tall facing forward and down at a hard crease drew as a sharp dark patch under a light from
# above. Laplacian-smoothed in place (welded positions, NOSE_TIP_PASSES, at most NOSE_TIP_CAP), the midline kept at x = 0.
_nz = np.zeros(NU, bool); _hu = np.zeros(NU, bool); _hu[_th.ravel()] = True
_nz = _hu & (np.abs(_uu[:, 0]) < 0.017) & (_uu[:, 2] - Z0_ > 1.5724) & (_uu[:, 2] - Z0_ < 1.5984) & (_uu[:, 1] < -0.091)
_p0 = _uu.copy(); _p = _uu.copy(); _mid5 = np.abs(_uu[:, 0]) < 1e-6
NOSE_CAP = float(_os.environ.get('NOSE_TIP_CAP', '0.0035'))      # r19: 3.5 mm (2 mm left a large dark underside facet)
for _ in range(int(_os.environ.get('NOSE_TIP_PASSES', '10'))):
    _a5 = np.zeros_like(_p); np.add.at(_a5, _E[:, 0], _p[_E[:, 1]]); np.add.at(_a5, _E[:, 1], _p[_E[:, 0]])
    _L5 = _a5 / np.maximum(_deg, 1)[:, None]; _p[_nz] = _p[_nz] + 0.5 * (_L5[_nz] - _p[_nz]); _p[_mid5 & _nz, 0] = 0
    _dm = _p - _p0; _nm = np.linalg.norm(_dm, axis=1, keepdims=True); _p = _p0 + _dm * np.minimum(1, NOSE_CAP / np.maximum(_nm, 1e-9))
_mv5 = _nz[_iu]; co[_mv5] = _p[_iu[_mv5]]
print('NOSE tip smoothed', int(_nz.sum()), 'positions, max mm', round(float(np.linalg.norm(_p - _p0, axis=1).max()) * 1000, 2))
# (3) midline fins (faces lying in x = 0 with area, left by the sliver snap) stood out of concave stretches as thin light lines in close-ups:
# each made degenerate, its apex moved onto its longest edge on the midline (at most 3 mm, repeated)
_k6 = np.round(co, 6); _u6, _i6 = np.unique(_k6, axis=0, return_inverse=True); _i6 = _i6.ravel(); _fins = []
_t6 = np.unique(np.sort(_i6[th_], axis=1), axis=0); _o6 = _u6.copy(); _nf = 0
for _it in range(int(_os.environ.get('FIN_ITERS', '20'))):
    _c6 = _u6[_t6]; _on = (np.abs(_c6[:, :, 0]) < 1e-7).all(1)
    _a6 = np.linalg.norm(np.cross(_c6[:, 1] - _c6[:, 0], _c6[:, 2] - _c6[:, 0]), axis=1) / 2; _fz = _c6.mean(1)[:, 2] - Z0_
    _fins = np.where(_on & (_a6 > 2e-9) & (_c6.mean(1)[:, 1] < -0.05) & (_fz > 1.43) & (_fz < 1.70))[0]
    if not len(_fins): break
    for _f in _fins:
        _v = _t6[_f]; _q = _u6[_v]; _el = [np.linalg.norm(_q[(j + 1) % 3] - _q[(j + 2) % 3]) for j in range(3)]; j = int(np.argmax(_el))
        _a, _b = _q[(j + 1) % 3], _q[(j + 2) % 3]; _dd = _b - _a; _tt = np.clip(np.dot(_q[j] - _a, _dd) / max(np.dot(_dd, _dd), 1e-18), 0, 1)
        _tgt = _a + _tt * _dd
        if np.linalg.norm(_tgt - _o6[_v[j]]) < 0.003: _u6[_v[j]] = _tgt; _nf += 1
_mv6 = (np.linalg.norm(_u6 - _o6, axis=1) > 0)[_i6]; co[_mv6] = _u6[_i6[_mv6]]
print('FINS collapsed', _nf, 'moves, left', len(_fins), 'max mm', round(float(np.linalg.norm(_u6 - _o6, axis=1).max()) * 1000, 2))
# PF7 upper lids (r5: eyes read wide): the head shell's eye-socket openings (boundary loops round each eyeball) - their upper rim vertices
# (above the eyeball centre) move down by LID_DOWN x their height share and LID_FWD forward, so the lash line covers more of the iris
from collections import defaultdict as _dd2
_ec2 = _dd2(int)
for a_, b_, c_ in th_:
    for e_ in ((a_, b_), (b_, c_), (c_, a_)): _ec2[(min(e_), max(e_))] += 1
_bv = np.unique([v for e_, n_ in _ec2.items() if n_ == 1 for v in e_]).astype(int)
_key2 = np.round(co, 5); _uk, _ik = np.unique(_key2, axis=0, return_inverse=True); _ik = _ik.ravel(); _cnt2 = np.bincount(_ik)
_bv = _bv[_cnt2[_ik[_bv]] == 1]          # open boundary only (not seams shared with another part)
LID_DOWN = float(_os.environ.get('LID_DOWN', '0.0016')); LID_FWD = float(_os.environ.get('LID_FWD', '0.0005')); _nl = 0
for sg in (1, -1):
    c_ = np.array([0.0275 * sg, -0.0801, 0.6884])
    rv = _bv[(np.linalg.norm(co[_bv] - c_, axis=1) < 0.022) & (co[_bv, 2] > c_[2] - 0.002)]
    if not len(rv): continue
    hgt = np.clip((co[rv, 2] - c_[2]) / 0.010, 0, 1); hx = np.clip(1 - np.abs(co[rv, 0] - c_[0]) / 0.016, 0, 1)
    w_ = hgt * hx
    co[rv, 2] -= LID_DOWN * w_; co[rv, 1] -= LID_FWD * w_; _nl += len(rv)
print('LIDS upper rim verts', _nl, 'down mm', LID_DOWN * 1000)
# eyeballs (the head's small closed components) 1.5 mm deeper, so the mesh's lids overlap them (they stared)
EYE_BACK = float(_os.environ.get('EYE_BACK', '0.003'))
hk = names.index('head'); par = np.arange(len(co))
def _f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a_, b_, c_ in tri[comp[tri[:, 0]] == hk]:
    r_ = _f(a_); par[_f(b_)] = r_; par[_f(c_)] = r_
hv_ = np.where(comp == hk)[0]; rt_ = np.array([_f(v) for v in hv_]); big_ = np.bincount(rt_).argmax()
ev_ = hv_[rt_ != big_]; co[ev_, 1] += EYE_BACK; print('EYES back', len(ev_), 'verts', EYE_BACK)
# PF2: the hair cap's lower side rows stretched down over the ears to jaw level (MM9's hair covers the ears; Meshy's cap stopped above
# them): per azimuth from the back, hair vertices within CAP_BAND of the cap's lowest point move down by (bottom - CAP_Z) x taper, then sit
# between 3 and 12 mm off the head surface. Positions only (the painted strands are vertical and simply lengthen).
kh2 = names.index('hair'); hv2 = np.where(comp == kh2)[0]; kh1 = names.index('head'); hh = np.where(comp == kh1)[0]
az = lambda P_: np.degrees(np.arctan2(np.abs(P_[:, 0]), P_[:, 1]))
ah, ahh = az(co[hv2]), az(co[hh])
BAND = float(_os.environ.get('CAP_BAND', '0.05')); nmv = 0
capz = lambda a: float(np.interp(a, [30, 50, 95, 122, 132], [0.600, 0.598, 0.603, 0.632, 0.650]))
cap = co[hv2, 2] > 0.60
for a0 in np.arange(30, 136, 3.0):
    sel = cap & (np.abs(ah - a0) < 1.5)
    if not sel.any(): continue
    zb = co[hv2[sel], 2].min(); tap = np.clip((a0 - 32) / 15, 0, 1) * np.clip((132 - a0) / 12, 0, 1)
    D_ = max(zb - capz(a0), 0) * tap
    if D_ <= 0: continue
    idx = hv2[sel]; tt = np.clip((zb + BAND - co[idx, 2]) / BAND, 0, 1); tt = tt * tt * (3 - 2 * tt); co[idx, 2] -= tt * D_
    hs = hh[(np.abs(ahh - a0) < 3)]
    for i in idx[tt > 0]:
        m = hs[np.abs(co[hs, 2] - co[i, 2]) < 0.006]
        if not len(m): continue
        rh = np.hypot(co[m, 0], co[m, 1]).max(); r = np.hypot(co[i, 0], co[i, 1]); rr = np.clip(r, rh + 0.003, rh + 0.012)
        ti = float(tt[list(idx).index(i)]); rr = rr * (1 - 0.7 * ti ** 2) + (rh + 0.0025) * 0.7 * ti ** 2      # the lowest rows tuck in: a rounded edge
        co[i, :2] *= rr / max(r, 1e-6)
    nmv += int((tt > 0).sum())
# the stretched band smoothed (Meshy's jagged cap rim became long flaps when pulled down): Laplacian over the hair part's edges on the moved
# vertices and their 2-ring, CAP_SMOOTH passes, then the 3 mm clearance off the head re-applied
ht2 = tri[comp[tri[:, 0]] == kh2]; e2 = np.unique(np.sort(np.vstack([ht2[:, [0, 1]], ht2[:, [1, 2]], ht2[:, [2, 0]]]), axis=1), axis=0)
_k2 = np.round(co, 6)
moved = np.zeros(len(co), bool); moved[hv2] = (co[hv2, 2] < 0.66) & (np.degrees(np.arctan2(np.abs(co[hv2, 0]), co[hv2, 1])) > 30)
sidemask = np.zeros(len(co), bool); sidemask[hv2] = np.degrees(np.arctan2(np.abs(co[hv2, 0]), co[hv2, 1])) > 26
for _ in range(2):
    nbm = moved.copy(); nbm[e2[:, 0][moved[e2[:, 1]]]] = True; nbm[e2[:, 1][moved[e2[:, 0]]]] = True; moved = nbm & sidemask
dg2 = np.zeros(len(co)); np.add.at(dg2, e2[:, 0], 1); np.add.at(dg2, e2[:, 1], 1)
for _ in range(int(_os.environ.get('CAP_SMOOTH', '8'))):
    acc = np.zeros_like(co); np.add.at(acc, e2[:, 0], co[e2[:, 1]]); np.add.at(acc, e2[:, 1], co[e2[:, 0]])
    L2 = acc / np.maximum(dg2, 1)[:, None]; co[moved] = co[moved] + 0.5 * (L2[moved] - co[moved])
from scipy.spatial import cKDTree as _KDh
_hk = _KDh(co[hh]); dd_, ii_ = _hk.query(co[moved]); inside = dd_ < 0.003
mv_ = np.where(moved)[0][inside]; dirv = co[mv_] - co[hh][ii_[inside]]; dirv /= np.maximum(np.linalg.norm(dirv, axis=1, keepdims=True), 1e-9)
co[mv_] = co[hh][ii_[inside]] + dirv * 0.003
print('CAP stretched over the ears: verts', nmv, 'band smoothed', int(moved.sum()), 'pushed off the skull', int(inside.sum()))
# face pass 2 (coordinator: a light flap of cap inside behind the ear at the braid top; jagged angular side flaps off the cheeks): the cap's
# open lower rim (the hair part's longest boundary loop, welded) is smoothed along the loop (height and offset, RIM_SMOOTH passes) and tucked
# onto the skin: rim positions sit RIM_GAP off the nearest head surface point; the next two rings follow by 0.6 / 0.3
from collections import defaultdict as _dd3
_kh = np.round(co, 6); _uh, _ih = np.unique(_kh, axis=0, return_inverse=True); _ih = _ih.ravel()
_th = _ih[ht2]; _eh = np.sort(np.vstack([_th[:, [0, 1]], _th[:, [1, 2]], _th[:, [2, 0]]]), 1); _ue, _ce = np.unique(_eh, axis=0, return_counts=True)
_nb = _dd3(list)
for a_, b_ in _ue[_ce == 1]: _nb[a_].append(b_); _nb[b_].append(a_)
_seen = set(); _loops = []
for v_ in list(_nb):
    if v_ in _seen or len(_nb[v_]) != 2: continue
    L_ = [v_]; _seen.add(v_); pv_, cu_ = None, v_
    while True:
        nx_ = [w for w in _nb[cu_] if w != pv_]
        if not nx_ or nx_[0] == v_ or nx_[0] in _seen or len(_nb[nx_[0]]) != 2: break
        _seen.add(nx_[0]); L_.append(nx_[0]); pv_, cu_ = cu_, nx_[0]
    _loops.append(L_)
rim_ = max(_loops, key=len); R_ = _uh[rim_].copy(); print('RIM loop', len(rim_), 'z', round(float(R_[:, 2].min()), 3), round(float(R_[:, 2].max()), 3))
for _ in range(int(_os.environ.get('RIM_SMOOTH', '12'))):
    R_ = 0.5 * R_ + 0.25 * (np.roll(R_, 1, 0) + np.roll(R_, -1, 0))
_hpts = co[hh]; _kd = _KDh(_hpts); GAP = float(_os.environ.get('RIM_GAP', '0.0015'))
def _tuck(P_):
    d_, i_ = _kd.query(P_); hp_ = _hpts[i_]; dv_ = np.c_[P_[:, 0], P_[:, 1], 0 * P_[:, 0]] - np.c_[hp_[:, 0], hp_[:, 1], 0 * hp_[:, 0]]
    rr_ = np.hypot(hp_[:, 0], hp_[:, 1]); out_ = np.c_[hp_[:, 0], hp_[:, 1], 0 * rr_] / np.maximum(rr_, 1e-6)[:, None]
    return np.c_[hp_[:, 0], hp_[:, 1], P_[:, 2]] + out_ * GAP
Rt_ = _tuck(R_); new_u = _uh.copy(); new_u[rim_] = Rt_
# rings
ring1 = set(); [ring1.update(_nb2) for _nb2 in []]
_adj = _dd3(set)
for t_ in _th:
    for a_ in t_:
        for b_ in t_:
            if a_ != b_: _adj[a_].add(b_)
r0 = set(rim_); r1 = set(w for v in rim_ for w in _adj[v]) - r0; r2 = set(w for v in r1 for w in _adj[v]) - r0 - r1
for ring_, wt_ in ((r1, 0.6), (r2, 0.3)):
    rl_ = np.array(sorted(ring_)); Pt_ = _tuck(_uh[rl_])
    # only pull inward (never push a ring row out), and only for rows below the cap's crown
    rad0 = np.hypot(_uh[rl_, 0], _uh[rl_, 1]); radt = np.hypot(Pt_[:, 0], Pt_[:, 1]); w_ = wt_ * (radt < rad0) * (_uh[rl_, 2] < 0.70)
    new_u[rl_] = _uh[rl_] * (1 - w_[:, None]) + Pt_ * w_[:, None]
mvh = (comp == kh2); co[mvh] = new_u[_ih[mvh]]
print('RIM tucked: rim', len(rim_), 'ring1', len(r1), 'ring2', len(r2), 'max move mm', round(float(np.linalg.norm(new_u - _uh, axis=1).max() * 1000), 1))
# PF2: the shins hidden in the skirt slimmed 15 % about each leg's axis above the hem + 4 cm (legs through the skirt by up to 0.9 cm in
# Cower/Death/Dead); the visible ankles and shoes are untouched
kl_ = names.index('legs'); HEMZ = float(_os.environ.get('HEM_Z', '-0.80'))
for sg_ in (1, -1):
    lv_ = np.where((comp == kl_) & (co[:, 0] * sg_ > 0))[0]
    if not len(lv_): continue
    ax_ = co[lv_][co[lv_, 2] > HEMZ + 0.04]
    if not len(ax_): continue
    cx_, cy_ = np.median(ax_[:, 0]), np.median(ax_[:, 1]); k_ = np.clip((co[lv_, 2] - (HEMZ + 0.04)) / 0.04, 0, 1) * 0.15
    co[lv_, 0] = cx_ + (co[lv_, 0] - cx_) * (1 - k_); co[lv_, 1] = cy_ + (co[lv_, 1] - cy_) * (1 - k_)
# face pass 2: midline cracks (the mirror seam's unwelded vertices and the sub-mm needle slivers dropped before the upload: open boundary
# edges under the nose, on the chin, forehead and the hair parting = the pale speck / dark notches): open-boundary vertices of the head and
# hair within CRACK_X of the midline (front half) snap onto x = 0, so each meets its mirror partner and the normals weld by position
CX_ = float(_os.environ.get('CRACK_X', '0.004')); ncr = 0
for part_ in ('head', 'hair'):
    if part_ not in names: continue
    kp_ = names.index(part_); tp_ = tri[comp[tri[:, 0]] == kp_]
    ek_ = np.round(co, 6); _uq, _iq = np.unique(ek_, axis=0, return_inverse=True); _iq = _iq.ravel()
    tq_ = _iq[tp_]; ee_ = np.sort(np.vstack([tq_[:, [0, 1]], tq_[:, [1, 2]], tq_[:, [2, 0]]]), 1); ue_, ce_ = np.unique(ee_, axis=0, return_counts=True)
    bq_ = np.unique(ue_[ce_ == 1]); sel_ = bq_[(np.abs(_uq[bq_, 0]) < CX_) & (np.abs(_uq[bq_, 0]) > 0) & (_uq[bq_, 1] < -0.02)]
    mv_ = np.isin(_iq, sel_) & (comp == kp_); co[mv_, 0] = 0; ncr += int(len(sel_))
print('CRACKS welded (midline boundary positions snapped)', ncr)
# face pass 2c: small holes left in the nose/mouth area (figure-8 boundaries after the dropped needle slivers): each connected group of
# head open-boundary edges there (front, |x| < 12 mm, z 0.60-0.66) under HOLE_MAX across collapses to its centroid, which closes it
from scipy.sparse import coo_matrix as _coo2
from scipy.sparse.csgraph import connected_components as _cc2
kp_ = names.index('head'); _Dt = D['tri']; _Do = D['orig']; tp_ = _Do[_Dt[comp[_Do[_Dt[:, 0]]] == kp_]]
ek_ = np.round(co, 6); _uq, _iq = np.unique(ek_, axis=0, return_inverse=True); _iq = _iq.ravel(); tq_ = _iq[tp_]
tq_ = tq_[(tq_[:, 0] != tq_[:, 1]) & (tq_[:, 1] != tq_[:, 2]) & (tq_[:, 0] != tq_[:, 2])]
ee_ = np.sort(np.vstack([tq_[:, [0, 1]], tq_[:, [1, 2]], tq_[:, [2, 0]]]), 1); ue_, ce_ = np.unique(ee_, axis=0, return_counts=True); be_ = ue_[ce_ == 1]
mb_ = _uq[be_].mean(1); be_ = be_[(np.abs(mb_[:, 0]) < 0.012) & (mb_[:, 2] > 0.60) & (mb_[:, 2] < 0.66) & (mb_[:, 1] < -0.09)]
nh_ = 0
if len(be_):
    vv_ = np.unique(be_); lid_ = {v: i for i, v in enumerate(vv_)}
    A_ = _coo2((np.ones(len(be_)), ([lid_[a] for a in be_[:, 0]], [lid_[b] for b in be_[:, 1]])), shape=(len(vv_), len(vv_)))
    ncomp_, lab_ = _cc2(A_, directed=False)
    for c_ in range(ncomp_):
        g_ = vv_[lab_ == c_]; P_ = _uq[g_]
        if np.ptp(P_, axis=0).max() > float(_os.environ.get('HOLE_MAX', '0.008')) or len(g_) < 3: continue
        cen_ = P_.mean(0); cen_[0] = 0 if np.abs(cen_[0]) < 0.002 else cen_[0]
        for v in g_: co[(_iq == v) & (comp == kp_)] = cen_
        nh_ += 1
print('HOLES collapsed', nh_)
# MOUTH2 (orchestrator pre-screen 2026-11-04 after the F7 lip patching failed twice: "a pointed triangular peak in the middle of the upper
# lip, the lips meeting in a jagged horizontal slit band, the lower lip a separate pad"): the mouth geometry is rebuilt BEFORE a fresh head
# paint (and never moved after it). (a) The head-shell positions in an ellipse round the closed slit (|x| < MRX, MRZ_UP above the slit line
# LZ, MRZ_DN below, front only, the nose base and nostrils outside) are Laplacian-relaxed in 3D (MITERS passes, full strength inside 60 %
# of the ellipse, eased to 0 at its rim): the folds, the tubercle peak, the slit groove and the separate lower-lip pad go, one smooth face
# surface remains. (b) Subtle lips are sculpted into that surface along -y (forward), as mm9_peasantboy_claude/scripts/lip_sculpt.py, scaled
# by t = 1 - (|x| / MHALF)^2: upper lip +UPL (centre 2.4 mm above LZ), lower lip +LOL (3.4 mm below), a fine closed groove at LZ (-GRV), the
# mentolabial dip (-0.6 mm, 10 mm below), a philtrum groove (-0.3 mm, |x| < 4 mm), the corners tucked (-0.8 mm) and turned up 0.8 mm into
# the cheeks. Positions only (UVs and weights unchanged); the new head paint is made on this surface.
if _os.environ.get('MOUTH2', '0') == '1':
    kp2 = names.index('head'); tp2 = _Do[_Dt[comp[_Do[_Dt[:, 0]]] == kp2]]
    ek2 = np.round(co, 6); uq2, iq2 = np.unique(ek2, axis=0, return_inverse=True); iq2 = iq2.ravel()
    t2 = iq2[tp2]; e2 = np.unique(np.sort(np.vstack([t2[:, [0, 1]], t2[:, [1, 2]], t2[:, [2, 0]]]), 1), axis=0); e2 = e2[e2[:, 0] != e2[:, 1]]
    hv2 = np.zeros(len(uq2), bool); hv2[iq2[comp == kp2]] = True
    LZ2 = float(_os.environ.get('MOUTH2_LZ', str(LZ))); MRX = float(_os.environ.get('MRX', '0.032'))
    MRU = float(_os.environ.get('MRZ_UP', '0.011')); MRD = float(_os.environ.get('MRZ_DN', '0.020'))
    X2, Y2, Z2 = uq2[:, 0], uq2[:, 1], uq2[:, 2]
    rz = np.where(Z2 > LZ2, (Z2 - LZ2) / MRU, (LZ2 - Z2) / MRD); r2 = np.sqrt((X2 / MRX) ** 2 + rz ** 2)
    nose2 = (Z2 > LZ2 + 0.009) & (np.abs(X2) < 0.013)
    w2 = np.clip((1 - r2) / 0.4, 0, 1); w2 = w2 * w2 * (3 - 2 * w2) * hv2 * (Y2 < -0.07) * ~nose2
    _dg0 = np.zeros(len(uq2)); np.add.at(_dg0, e2.ravel(), 1); w2 = w2 * (_dg0 > 0)      # unused positions stay
    P2 = uq2.copy(); P20 = uq2.copy()
    for _ in range(int(_os.environ.get('MITERS', '40'))):
        acc = np.zeros_like(P2); dg = np.zeros(len(P2))
        np.add.at(acc, e2[:, 0], P2[e2[:, 1]]); np.add.at(acc, e2[:, 1], P2[e2[:, 0]]); np.add.at(dg, e2[:, 0], 1); np.add.at(dg, e2[:, 1], 1)
        Lp = acc / np.maximum(dg, 1)[:, None]
        P2 = P2 + 0.5 * w2[:, None] * (Lp - P2)
        P2[np.abs(P20[:, 0]) < 1e-7, 0] = 0
    HALF2 = float(_os.environ.get('MHALF', '0.022'))
    def g_(v, m, s): return np.exp(-0.5 * ((v - m) / s) ** 2)
    xa = np.abs(P2[:, 0]); zz = P2[:, 2] - LZ2; tt = np.clip(1 - (xa / HALF2) ** 2, 0, 1)
    UPL = float(_os.environ.get('UPL', '0.0012')); LOL = float(_os.environ.get('LOL', '0.0018')); GRV = float(_os.environ.get('GRV', '0.0004'))
    off = (UPL * g_(zz, float(_os.environ.get('UPZ', '0.0026')), float(_os.environ.get('UPS', '0.0020'))) + LOL * g_(zz, float(_os.environ.get('LOZ', '-0.0036')), float(_os.environ.get('LOS', '0.0025'))) - GRV * g_(zz, 0.0, float(_os.environ.get('GRS', '0.0008')))) * tt
    off += -0.0006 * g_(zz, -0.010, 0.0025) * np.clip(1 - (xa / 0.020) ** 2, 0, 1)
    off += -float(_os.environ.get('PHG', '0.0003')) * (xa < 0.004) * np.clip((zz - 0.004) / 0.002, 0, 1) * np.clip((0.012 - zz) / 0.002, 0, 1)
    corner = g_(xa, HALF2, 0.003) * g_(zz, 0.0, 0.002)
    off += -0.0008 * corner
    dz2 = 0.0008 * g_(xa, HALF2 - 0.002, 0.004) * g_(zz, 0.0, 0.003)
    wsc = np.clip((1 - r2) / 0.25, 0, 1) * hv2 * (Y2 < -0.07) * ~nose2 * (_dg0 > 0)
    P2[:, 1] -= off * wsc; P2[:, 2] += dz2 * wsc
    mvd = np.linalg.norm(P2 - P20, axis=1)
    for v in np.where(mvd > 1e-9)[0]: co[(iq2 == v) & (comp == kp2)] = P2[v]
    print('MOUTH2 relaxed+sculpted positions', int((mvd > 1e-9).sum()), 'max mm', round(float(mvd.max()) * 1000, 2), 'LZ', round(LZ2, 4))
# NOSE2 (orchestrator pre-screen 2026-11-04: "a sharp pointed triangular wedge between the nostrils (columella/flap geometry)"): the
# columella - head-shell positions under the nose tip between the nostrils (|x| < NC_X, z NC_Z0..NC_Z1, behind the tip front, facing down) -
# Laplacian-relaxed in 3D (NC_ITERS passes, eased at the zone's edge, at most NC_CAP) into a rounded septum; the bridge, the tip's front
# and the wings are outside the zone. Positions only, before the fresh head paint.
if _os.environ.get('NOSE2', '0') == '1':
    kp3 = names.index('head'); tp3 = _Do[_Dt[comp[_Do[_Dt[:, 0]]] == kp3]]
    ek3 = np.round(co, 6); uq3, iq3 = np.unique(ek3, axis=0, return_inverse=True); iq3 = iq3.ravel()
    t3 = iq3[tp3]; t3 = t3[(t3[:, 0] != t3[:, 1]) & (t3[:, 1] != t3[:, 2]) & (t3[:, 0] != t3[:, 2])]
    e3 = np.unique(np.sort(np.vstack([t3[:, [0, 1]], t3[:, [1, 2]], t3[:, [2, 0]]]), 1), axis=0)
    fn3 = np.cross(uq3[t3[:, 1]] - uq3[t3[:, 0]], uq3[t3[:, 2]] - uq3[t3[:, 0]]); vn3 = np.zeros_like(uq3)
    for c_ in range(3): np.add.at(vn3, t3[:, c_], fn3)
    vn3 /= np.maximum(np.linalg.norm(vn3, axis=1, keepdims=True), 1e-12)
    NCX = float(_os.environ.get('NC_X', '0.0065')); NZ0 = float(_os.environ.get('NC_Z0', '0.6345')); NZ1 = float(_os.environ.get('NC_Z1', '0.6520'))
    X3, Y3, Z3 = uq3[:, 0], uq3[:, 1], uq3[:, 2]
    w3 = (np.clip((NCX - np.abs(X3)) / 0.002, 0, 1) * np.clip((Z3 - NZ0) / 0.002, 0, 1) * np.clip((NZ1 - Z3) / 0.002, 0, 1) * (Y3 < -0.088)
          * np.clip((-vn3[:, 2] - 0.15) / 0.25, 0, 1))
    dg3 = np.zeros(len(uq3)); np.add.at(dg3, e3.ravel(), 1); w3 = w3 * (dg3 > 0)
    P3 = uq3.copy(); P30 = uq3.copy(); CAP3 = float(_os.environ.get('NC_CAP', '0.003'))
    for _ in range(int(_os.environ.get('NC_ITERS', '20'))):
        acc = np.zeros_like(P3); dg = np.zeros(len(P3))
        np.add.at(acc, e3[:, 0], P3[e3[:, 1]]); np.add.at(acc, e3[:, 1], P3[e3[:, 0]]); np.add.at(dg, e3[:, 0], 1); np.add.at(dg, e3[:, 1], 1)
        P3 = P3 + 0.5 * w3[:, None] * (acc / np.maximum(dg, 1)[:, None] - P3)
        dv = P3 - P30; dl = np.linalg.norm(dv, axis=1, keepdims=True); P3 = P30 + dv * np.minimum(1, CAP3 / np.maximum(dl, 1e-12))
        P3[np.abs(P30[:, 0]) < 1e-7, 0] = 0
    md3 = np.linalg.norm(P3 - P30, axis=1)
    for v in np.where(md3 > 1e-9)[0]: co[(iq3 == v) & (comp == kp3)] = P3[v]
    print('NOSE2 columella relaxed positions', int((md3 > 1e-9).sum()), 'max mm', round(float(md3.max()) * 1000, 2))
D['co'] = co[D['orig']]
# degenerate faces (the collapsed midline fins, the closed slit's slivers) dropped: their normals lit as a pale speck under the nose (r9)
_c = D['co'][D['tri']]; _ar = np.linalg.norm(np.cross(_c[:, 1] - _c[:, 0], _c[:, 2] - _c[:, 0]), axis=1) / 2
_keep = _ar > 1e-10
for _k in ('tri', 'mat', 'inner'): D[_k] = D[_k][_keep]
print('DEGENERATE faces dropped', int((~_keep).sum()))
np.savez(OUT, **D); print('saved', OUT)
