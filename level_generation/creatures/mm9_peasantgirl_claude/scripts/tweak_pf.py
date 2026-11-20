#!/usr/bin/env python3
"""Geometry tweaks after the paint (UVs unchanged, the paint moves with the mesh): the mirrored head meets itself at x = 0 at an angle, a crease
that shaded as a dark line down the chin and a light strip on the nose. Vertices within BAND of the midline on the face are pulled forward
(depth only, valleys only, at most 3 mm), so the halves meet smoothly; ridges (the nose) are left. Args: <asm npz> <uv_tex npz> <out npz> [band m] [passes]"""
import sys
import numpy as np
A, U, OUT = sys.argv[1:4]; CAP = 0.003; BAND = float(sys.argv[4]) if len(sys.argv) > 4 else 0.010; PASSES = int(sys.argv[5]) if len(sys.argv) > 5 else 8
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
SNAP = 0.0025
for part in ('head', 'coif', 'dress', 'skirt', 'lining'):
    k = names.index(part); q = (comp == k) & (np.abs(co[:, 0]) < SNAP) & (np.abs(co[:, 0]) > 0)
    co[q, 0] = 0; print('SNAP', part, int(q.sum()))
# hand stubs: the STUB cut left a zig-zag rim. The rim goes onto one ring STUB behind the wrist (inside the forearm), the next rows
# are relaxed along the arm; UVs are unchanged (the stretched skin sits inside the cuff)
from collections import defaultdict
k = names.index('hands'); t = tri[comp[tri[:, 0]] == k]
ec = defaultdict(int)
for a, b, c in t:
    for e in ((a, b), (b, c), (c, a)): ec[(min(e), max(e))] += 1
rim = np.unique([v for e, n in ec.items() if n == 1 for v in e])
e = np.array([e for e in ec]); wr0, ax0 = S['wr'], S['ax']; STUB = 0.035
for sg in (1, -1):
    fd = ax0 * [sg, 1, 1]; w = wr0 * [sg, 1, 1]
    side = (comp == k) & (co[:, 0] * sg > 0)
    al = (co - w) @ fd
    r_ = rim[side[rim]]
    co[r_] += ((-STUB - al[r_])[:, None]) * fd
    mov = np.where(side & (al < -0.012))[0]; mov = np.setdiff1d(mov, r_)
    for _ in range(6):
        al = (co - w) @ fd; acc = np.zeros(len(co)); deg = np.zeros(len(co))
        np.add.at(acc, e[:, 0], al[e[:, 1]]); np.add.at(acc, e[:, 1], al[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        tgt = acc / np.maximum(deg, 1)
        co[mov] += ((0.5 * (tgt[mov] - al[mov]))[:, None]) * fd
    print('STUB rim', sg, len(r_), 'relaxed', len(mov))
# mouth (orchestrator review 2026-11-02: a protruding pout, lips pushed forward into a bulb): the lips' front surface is compared with a
# heavily smoothed copy of it (nose and chin outside the box hold it), and every vertex of the mouth column (lips and the cavity behind them)
# moves back by the lips' excess at its (x, z), feathered at the box edge, at most 6 mm: the lips go back onto the face without folding the
# cavity through them. Positions only (UVs and weights unchanged).
import os as _os
from scipy.spatial import cKDTree as _KD
MZ0, MZ1, MX = 0.580, 0.622, 0.036
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
EC = 0.6627; EX = 0.0266
crease = (comp == kh_) & ~_eye & (np.abs(np.abs(co[:, 0]) - EX) < 0.024) & (co[:, 2] > EC + 0.004) & (co[:, 2] < EC + 0.024) & (co[:, 1] < -0.08)
print('EYE CREASE smoothed', int(crease.sum()), 'verts, max mm', round(_smooth(crease, int(_os.environ.get('CREASE_PASSES', '12')), 0.0035) * 1000, 2))
nost = (comp == kh_) & (np.abs(co[:, 0]) > 0.003) & (np.abs(co[:, 0]) < 0.020) & (co[:, 2] > 0.617) & (co[:, 2] < 0.629) & (co[:, 1] < -0.105) & (co[:, 1] > -0.134)
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
LZ = float(_os.environ.get('MOUTH_SLIT', '1.5334')) + Z0_
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
fi_ = np.where(free)[0]; loc = -np.ones(NU, int); loc[fi_] = np.arange(len(fi_))
r_, c_, v_ = [], [], []; rhs = np.zeros((len(fi_), 3)); rim = np.zeros(NU, bool)
for a_, b_ in _E:
    for p_, q_ in ((a_, b_), (b_, a_)):
        if not free[p_]: continue
        if free[q_]: r_.append(loc[p_]); c_.append(loc[q_]); v_.append(-1.0)
        else: rhs[loc[p_]] += _uu[q_]; rim[q_] = True
r_ += list(range(len(fi_))); c_ += list(range(len(fi_))); v_ += list(_deg[fi_])
Lm = _coo((v_, (r_, c_)), shape=(len(fi_), len(fi_))).tocsr()
sol = np.stack([_spsolve(Lm, rhs[:, k]) for k in range(3)], -1)
phi = _spsolve(Lm, np.ones(len(fi_))); phi /= max(phi.max(), 1e-12)
DOME = float(_os.environ.get('MOUTH_DOME', '0.0025')); GROOVE = float(_os.environ.get('MOUTH_GROOVE', '0.0007'))
newp = sol.copy(); newp[:, 1] = sol[:, 1] - DOME * np.sqrt(phi)
zsl = LZ + 4.0 * newp[:, 0] ** 2
newp[:, 1] += GROOVE * np.exp(-((newp[:, 2] - zsl) / 0.0009) ** 2) * np.clip(1 - np.abs(newp[:, 0]) / 0.024, 0, 1)
_uu[fi_] = newp; _mv = free[_iu]; co[_mv] = _uu[_iu[_mv]]
print('MOUTH closed (unfolded): cavity positions', len(fi_), 'rim', int(rim.sum()), 'rim y', np.round(np.percentile(_uu[rim, 1], [0, 100]), 4).tolist())
# (2) the nose tip and underside: a facet 9 mm tall facing forward and down at a hard crease drew as a sharp dark patch under a light from
# above. Laplacian-smoothed in place (welded positions, NOSE_TIP_PASSES, at most NOSE_TIP_CAP), the midline kept at x = 0.
_nz = np.zeros(NU, bool); _hu = np.zeros(NU, bool); _hu[_th.ravel()] = True
_nz = _hu & (np.abs(_uu[:, 0]) < 0.017) & (_uu[:, 2] - Z0_ > 1.545) & (_uu[:, 2] - Z0_ < 1.580) & (_uu[:, 1] < -0.112)
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
_k6 = np.round(co, 6); _u6, _i6 = np.unique(_k6, axis=0, return_inverse=True); _i6 = _i6.ravel()
_t6 = np.unique(np.sort(_i6[th_], axis=1), axis=0); _o6 = _u6.copy(); _nf = 0
for _it in range(20):
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
# eyeballs (the head's small closed components) 1.5 mm deeper, so the mesh's lids overlap them (they stared)
EYE_BACK = 0.0015
hk = names.index('head'); par = np.arange(len(co))
def _f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a_, b_, c_ in tri[comp[tri[:, 0]] == hk]:
    r_ = _f(a_); par[_f(b_)] = r_; par[_f(c_)] = r_
hv_ = np.where(comp == hk)[0]; rt_ = np.array([_f(v) for v in hv_]); big_ = np.bincount(rt_).argmax()
ev_ = hv_[rt_ != big_]; co[ev_, 1] += EYE_BACK; print('EYES back', len(ev_), 'verts', EYE_BACK)
D['co'] = co[D['orig']]
np.savez(OUT, **D); print('saved', OUT)
