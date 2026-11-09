#!/usr/bin/env python3
"""PF1 (no cuffs or hand stubs: those PF8 steps dropped). Geometry tweaks after the paint (UVs unchanged, the paint moves with the mesh): the mirrored head meets itself at x = 0 at an angle, a crease
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
    _k0 = np.round(co, 5); _u0, _i0, _c0 = np.unique(_k0, axis=0, return_inverse=True, return_counts=True)
    sel = (comp == k) & (np.abs(co[:, 0]) < BAND) & (co[:, 1] < -0.05) & (_c0[_i0.ravel()] == 1)      # PF1: part seams stay
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
# PF1: Meshy's small human ears poke through the open sides of the hood (pink tips beside the face): pressed into the skull by Laplacian
# smoothing round the ear centre (as PF8's flatten_ears). Vertices shared with another part (the hood seam) stay where they are.
import os
EC = np.array([float(x) for x in os.environ.get('EAR_C', '0.076,-0.028,1.580').split(',')]) + [0, 0, -0.9297]
kh = names.index('head')
# the ear's outward reach clamped to the skull's (|x| <= XMAX in the ear zone), head vertices and their coincident hood twins together
XMAX = float(os.environ.get('EAR_XMAX', '0.063'))
key = np.round(co, 5); _u, _inv = np.unique(key, axis=0, return_inverse=True); _inv = _inv.ravel()
zone = (co[:, 1] > EC[1] - 0.04) & (co[:, 1] < EC[1] + 0.04) & (np.abs(co[:, 2] - EC[2]) < 0.045) & (np.abs(co[:, 0]) > XMAX)
hk = np.zeros(len(_u), bool); hk[_inv[(comp == kh) & zone]] = True
mv = hk[_inv] & zone
dz_ = np.abs(co[:, 2] - EC[2]); fall = np.clip((0.045 - dz_) / 0.015, 0, 1)        # eased at the zone's top and bottom
newx = np.sign(co[:, 0]) * (XMAX + (np.abs(co[:, 0]) - XMAX) * (1 - fall))
print('EARS clamped', int(mv.sum()), 'verts, max mm', round(float(np.abs(newx - co[:, 0])[mv].max()) * 1000, 1))
co[mv, 0] = newx[mv]
# PF1: the mouth was modelled slightly open (a slit into a cavity, Meshy's teeth pieces inside) while the references close the lips. The
# recessed cavity vertices come forward to the lips' front (closed lips, flush), the teeth pieces go 15 mm back out of sight.
Z0_ = -0.9297; LZ = 1.552 + Z0_
hp = np.where((comp == kh) & (np.abs(co[:, 0]) < 0.03) & (np.abs(co[:, 2] - LZ) < 0.016) & (co[:, 1] < -0.04))[0]
# pieces of the head part: the teeth are the small components at the mouth
_k2 = np.round(co, 5); _u2, _i2 = np.unique(_k2, axis=0, return_inverse=True); _i2 = _i2.ravel(); par2 = np.arange(len(_u2))
def f2(a):
    while par2[a] != a: par2[a] = par2[par2[a]]; a = par2[a]
    return a
for t_ in tri[comp[tri[:, 0]] == kh]:
    a_ = f2(_i2[t_[0]]); par2[f2(_i2[t_[1]])] = a_; par2[f2(_i2[t_[2]])] = a_
rt2 = np.array([f2(_i2[v]) for v in range(len(co))]); sizes = np.bincount(rt2[comp == kh], minlength=len(_u2))
teeth = (comp == kh) & (sizes[rt2] < 300) & (np.abs(co[:, 0]) < 0.035) & (np.abs(co[:, 2] - LZ) < 0.02)
shellm = np.isin(hp, np.where(~teeth)[0]); hp = hp[shellm]
P2 = co[hp]; cavm = np.zeros(len(co), bool)
for i_ in range(len(hp)):
    d_ = np.hypot(P2[:, 0] - P2[i_, 0], P2[:, 2] - P2[i_, 2]); nb_ = d_ < 0.0035
    if P2[i_, 1] - P2[nb_, 1].min() > 0.002: cavm[hp[i_]] = True
# nose fix 2026-11-02 (user: "double textures" on the lip): pushed straight forward, the cavity's walls (6 cm deep) piled up at the rim of
# the opening as folded faces, and the flat plate between the lips shaded as a lighter tongue-like oval inside the lips. Now the cavity is
# closed as one unfolded surface: its vertices (welded positions) spread over the opening by a Tutte embedding in (x, z) (the rim held), the
# depth a harmonic fill of the rim's plus a dome (MOUTH_DOME m) so it continues the lips' fronts, and a shallow groove (MOUTH_GROOVE m)
# along the lip line at MOUTH_SLIT (m over the soles; the repaint's dark lip line), so the closed lips read as two lips meeting at a line.
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
_ku = np.round(co, 5); _uu, _iu = np.unique(_ku, axis=0, return_inverse=True); _iu = _iu.ravel(); NU = len(_uu)
_th = _iu[tri[(comp[tri[:, 0]] == kh) & ~teeth[tri].any(1)]]
_E = np.unique(np.sort(np.vstack([_th[:, [0, 1]], _th[:, [1, 2]], _th[:, [2, 0]]]), axis=1), axis=0); _E = _E[_E[:, 0] != _E[:, 1]]
free = np.zeros(NU, bool); free[_iu[cavm]] = True
# the rest of the sack: shell positions hidden from the front (front z-buffer of the head shell, 0.25 mm grid, 1.5 mm behind) connected to
# the cavity through hidden positions; otherwise its deep walls (y -6 cm) are rim and drag the closed surface back into a pucker
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
from scipy.ndimage import grey_erosion as _ge
_Zb = _ge(_Zb, size=3)
_ix = np.clip(np.round((_uu[:, 0] - _X0) / _RES).astype(int), 0, _NX - 1); _iz = np.clip(np.round((_uu[:, 2] - _ZL) / _RES).astype(int), 0, _NZ - 1)
_inside = (np.abs(_uu[:, 0]) < 0.045) & (np.abs(_uu[:, 2] - LZ) < 0.04)
hidden = _inside & (_uu[:, 1] - _Zb[_iz, _ix] > 0.0015)
_adj = [[] for _ in range(NU)]
for a_, b_ in _E: _adj[a_].append(b_); _adj[b_].append(a_)
_st = list(np.where(free)[0])
while _st:
    _v = _st.pop()
    for _w in _adj[_v]:
        if hidden[_w] and not free[_w]: free[_w] = True; _st.append(_w)
fi_ = np.where(free)[0]; loc = -np.ones(NU, int); loc[fi_] = np.arange(len(fi_))
deg_ = np.bincount(_E.ravel(), minlength=NU).astype(float)
r_, c_, v_ = [], [], []; rhs = np.zeros((len(fi_), 3)); rim = np.zeros(NU, bool)
for a_, b_ in _E:
    for p_, q_ in ((a_, b_), (b_, a_)):
        if not free[p_]: continue
        if free[q_]: r_.append(loc[p_]); c_.append(loc[q_]); v_.append(-1.0)
        else: rhs[loc[p_]] += _uu[q_]; rim[q_] = True
r_ += list(range(len(fi_))); c_ += list(range(len(fi_))); v_ += list(deg_[fi_])
Lm = coo_matrix((v_, (r_, c_)), shape=(len(fi_), len(fi_))).tocsr()
sol = np.stack([spsolve(Lm, rhs[:, k]) for k in range(3)], -1)                 # x, z: Tutte; y: harmonic
phi = spsolve(Lm, np.ones(len(fi_))); phi /= max(phi.max(), 1e-12)          # dome profile, 0 at the rim, 1 in the middle
DOME = float(os.environ.get('MOUTH_DOME', '0.0025')); GROOVE = float(os.environ.get('MOUTH_GROOVE', '0.0007'))
SLIT = float(os.environ.get('MOUTH_SLIT', '1.5525')) + Z0_
newp = sol.copy(); newp[:, 1] = sol[:, 1] - DOME * np.sqrt(phi)
zsl = SLIT + 4.0 * newp[:, 0] ** 2
newp[:, 1] += GROOVE * np.exp(-((newp[:, 2] - zsl) / 0.0009) ** 2) * np.clip(1 - np.abs(newp[:, 0]) / 0.024, 0, 1)
_up = _uu.copy(); _up[fi_] = newp
mvd = free[_iu]; co[mvd] = _up[_iu[mvd]]
co[teeth, 1] += 0.015
print('MOUTH closed (unfolded): cavity positions', len(fi_), 'rim', int(rim.sum()), 'rim z', np.round(np.percentile(_uu[rim, 2] - Z0_, [0, 100]), 4).tolist(), 'rim y', np.round(np.percentile(_uu[rim, 1], [0, 100]), 4).tolist(),
      'teeth verts back', int(teeth.sum()))
# PF1: the chin's large Meshy facets (a grey diamond under the lip in close-ups) and the pouting lips (face fix 2026-11-02): Laplacian-smoothed
# in place up to the upper lip (MOUTH_TOP), part seams held
_k3 = np.round(co, 5); _u3, _i3, _c3 = np.unique(_k3, axis=0, return_inverse=True, return_counts=True); _i3 = _i3.ravel()
_zs = co[:, 2] - Z0_
chin = (comp == kh) & (np.abs(co[:, 0]) < 0.035) & (_c3[_i3] == 1) & (((_zs > 1.470) & (_zs < 1.538) & (co[:, 1] < -0.04))
                                                                   | ((_zs >= 1.538) & (_zs < float(os.environ.get('MOUTH_TOP', '1.575'))) & (co[:, 1] < -0.105)))
tch = tri[comp[tri[:, 0]] == kh]; ech = np.unique(np.sort(np.vstack([tch[:, [0, 1]], tch[:, [1, 2]], tch[:, [2, 0]]]), axis=1), axis=0)
dg = np.zeros(len(co)); np.add.at(dg, ech[:, 0], 1); np.add.at(dg, ech[:, 1], 1)
c0 = co.copy()
for _ in range(int(os.environ.get('CHIN_PASSES', '10'))):
    acc = np.zeros_like(co); np.add.at(acc, ech[:, 0], co[ech[:, 1]]); np.add.at(acc, ech[:, 1], co[ech[:, 0]])
    L_ = acc / np.maximum(dg, 1)[:, None]; co[chin] = co[chin] + 0.5 * (L_[chin] - co[chin])
    co[chin & (np.abs(c0[:, 0]) < 1e-6), 0] = 0
    dmv = co - c0; nmv = np.linalg.norm(dmv, axis=1, keepdims=True); co = c0 + dmv * np.minimum(1, 0.004 / np.maximum(nmv, 1e-9))      # at most 4 mm
print('CHIN smoothed', int(chin.sum()), 'verts, max mm', round(float(np.linalg.norm(co - c0, axis=1).max()) * 1000, 2))
# nose fix 2026-11-02: the nose tip turned into its underside (a 1.6 cm facet facing forward and down, Meshy's nostril notches along its
# edges) at a hard crease, so from the front the underside drew as a sharp-edged dark triangle under any light from above. The tip and
# underside, and the bridge (welded positions), Laplacian-smoothed in place (NOSE_PASSES, at most 2 mm), the midline kept at x = 0.
_k5 = np.round(co, 5); _u5, _i5 = np.unique(_k5, axis=0, return_inverse=True); _i5 = _i5.ravel()
_t5 = _i5[tri[(comp[tri[:, 0]] == kh) & ~teeth[tri].any(1)]]
_e5 = np.unique(np.sort(np.vstack([_t5[:, [0, 1]], _t5[:, [1, 2]], _t5[:, [2, 0]]]), axis=1), axis=0); _e5 = _e5[_e5[:, 0] != _e5[:, 1]]
_d5 = np.bincount(_e5.ravel(), minlength=len(_u5)).astype(float)
_hu = np.zeros(len(_u5), bool); _hu[_t5.ravel()] = True
_nz = _hu & (np.abs(_u5[:, 0]) < 0.017) & (_u5[:, 2] - Z0_ > 1.572) & (_u5[:, 2] - Z0_ < 1.604) & (_u5[:, 1] < -0.112)
# and the bridge between the eyes: a flat facet there caught the light as a pale rectangle up to the brows
_nz |= _hu & (np.abs(_u5[:, 0]) < 0.013) & (_u5[:, 2] - Z0_ > 1.612) & (_u5[:, 2] - Z0_ < 1.668) & (_u5[:, 1] < -0.095)
_p0 = _u5.copy(); _p = _u5.copy(); _mid5 = np.abs(_u5[:, 0]) < 1e-6
for _ in range(int(os.environ.get('NOSE_PASSES', '6'))):
    _a5 = np.zeros_like(_p); np.add.at(_a5, _e5[:, 0], _p[_e5[:, 1]]); np.add.at(_a5, _e5[:, 1], _p[_e5[:, 0]])
    _L5 = _a5 / np.maximum(_d5, 1)[:, None]; _p[_nz] = _p[_nz] + 0.5 * (_L5[_nz] - _p[_nz]); _p[_mid5 & _nz, 0] = 0
    _dm = _p - _p0; _nm = np.linalg.norm(_dm, axis=1, keepdims=True); _p = _p0 + _dm * np.minimum(1, 0.002 / np.maximum(_nm, 1e-9))
_mv5 = _nz[_i5]; co[_mv5] = _p[_i5[_mv5]]
print('NOSE smoothed', int(_nz.sum()), 'positions, max mm', round(float(np.linalg.norm(_p - _p0, axis=1).max()) * 1000, 2))
# eye area (r23, coordinator review: "grey speck at the inner end of each brow"): the upper inner corner of each socket ended in a spike,
# Laplacian-smoothed in a 9 mm disk (at most 3 mm). (Smoothing the lower lid's shelf, and pushing the eyeball's lower part back behind the
# lid, both opened a dark notch into the socket under the iris and were dropped.)
_k7 = np.round(co, 5); _u7, _i7 = np.unique(_k7, axis=0, return_inverse=True); _i7 = _i7.ravel()
_t7 = _i7[tri[(comp[tri[:, 0]] == kh) & ~teeth[tri].any(1)]]
_par7 = np.arange(len(_u7))
def _f7(a):
    while _par7[a] != a: _par7[a] = _par7[_par7[a]]; a = _par7[a]
    return a
for _a, _b, _c in _t7: _r = _f7(_a); _par7[_f7(_b)] = _r; _par7[_f7(_c)] = _r
_hv7 = np.unique(_t7); _rt7 = np.array([_f7(v) for v in range(len(_u7))]); _big7 = np.bincount(_rt7[_hv7]).argmax()
_shell7 = np.zeros(len(_u7), bool); _shell7[_hv7] = True; _shell7 &= _rt7 == _big7
_lid = 0
# the lower lid: the eyeball sits in a deep socket pocket of the shell whose lower rim is a jagged fold, so below the iris the ball
# showed in a jagged crescent that shaded brighter than the lid. The ball's positions under a smooth lower-lid curve (LID_DZ under the
# ball centre at the iris, curving up 45 m^-1 * dx^2 to the corners) go LID_BACK behind, eased over 0.5 mm: below the curve the lid's own
# surface (or the pocket wall, painted as skin shadow by project_face_pf1.py) shows, and the lid line follows the ball's finer mesh.
# (Tried and dropped: smoothing the shelf, a biharmonic relax of the lower socket, laying the ball onto the shell.)
LID_DZ = float(os.environ.get('LID_DZ', '0.0050')); LID_BACK = float(os.environ.get('LID_BACK', '0.0030')); _lid = 0
for _sg in (1, -1):
    _eb = _hv7[(_rt7[_hv7] != _big7) & (np.sign(_u7[_hv7, 0]) == _sg) & (np.abs(_u7[_hv7, 2] - (1.6136 + Z0_)) < 0.02) & (np.abs(_u7[_hv7, 0]) > 0.012) & (np.abs(_u7[_hv7, 0]) < 0.05)]
    if len(_eb) < 50: continue
    _c7 = (_u7[_eb].max(0) + _u7[_eb].min(0)) / 2
    _dx = _u7[_eb, 0] - _c7[0]; _dz = _u7[_eb, 2] - _c7[2]
    _w = np.clip(((-LID_DZ + 45.0 * _dx ** 2) - _dz) / 0.0005, 0, 1)
    _u7[_eb, 1] += LID_BACK * _w; _lid += int((_w > 0).sum())
print('EYES lower lid: ball positions back', _lid)
_e7 = np.unique(np.sort(np.vstack([_t7[:, [0, 1]], _t7[:, [1, 2]], _t7[:, [2, 0]]]), axis=1), axis=0); _e7 = _e7[_e7[:, 0] != _e7[:, 1]]
_d7 = np.bincount(_e7.ravel(), minlength=len(_u7)).astype(float)
_sp = _shell7 & (np.hypot(np.abs(_u7[:, 0]) - 0.022, _u7[:, 2] - (1.634 + Z0_)) < 0.009) & (_u7[:, 1] < -0.095)
_q0 = _u7.copy(); _q = _u7.copy()
for _ in range(8):
    _a7 = np.zeros_like(_q); np.add.at(_a7, _e7[:, 0], _q[_e7[:, 1]]); np.add.at(_a7, _e7[:, 1], _q[_e7[:, 0]])
    _L7 = _a7 / np.maximum(_d7, 1)[:, None]; _q[_sp] = _q[_sp] + 0.5 * (_L7[_sp] - _q[_sp])
    _dm7 = _q - _q0; _nm7 = np.linalg.norm(_dm7, axis=1, keepdims=True); _q = _q0 + _dm7 * np.minimum(1, 0.003 / np.maximum(_nm7, 1e-9))
_u7 = _q
# the clamped ear plates (r23, coordinator review: "the hood-edge patch in 3/4 and side"): the plate was clamped flat at |x| 6.3 cm and met
# the cheek at an angle, a hard-shaded facet whatever the paint. Its head positions (not those shared with the hood) Laplacian-smoothed
# into the cheek (EAR_PASSES, at most 4 mm), then held inside |x| <= 6.3 cm so the ear does not come back through the hood.
_sc7 = np.zeros(len(_u7), bool); _sc7[_i7[tri[comp[tri[:, 0]] == names.index('scarf')]].ravel()] = True
_ez = _shell7 & ~_sc7 & (np.abs(_u7[:, 0]) > 0.050) & (_u7[:, 2] - Z0_ > 1.530) & (_u7[:, 2] - Z0_ < 1.630) & (_u7[:, 1] > -0.075) & (_u7[:, 1] < 0.02)
_q0 = _u7.copy(); _q = _u7.copy()
for _ in range(int(os.environ.get('EAR_PASSES', '10'))):
    _a7 = np.zeros_like(_q); np.add.at(_a7, _e7[:, 0], _q[_e7[:, 1]]); np.add.at(_a7, _e7[:, 1], _q[_e7[:, 0]])
    _L7 = _a7 / np.maximum(_d7, 1)[:, None]; _q[_ez] = _q[_ez] + 0.5 * (_L7[_ez] - _q[_ez])
    _q[_ez, 0] = np.sign(_q[_ez, 0]) * np.minimum(np.abs(_q[_ez, 0]), XMAX)
    _dm7 = _q - _q0; _nm7 = np.linalg.norm(_dm7, axis=1, keepdims=True); _q = _q0 + _dm7 * np.minimum(1, 0.004 / np.maximum(_nm7, 1e-9))
print('EAR plates smoothed', int(_ez.sum()), 'positions, max mm', round(float(np.linalg.norm(_q - _q0, axis=1).max()) * 1000, 2))
_u7 = _q
_ch7 = np.linalg.norm(_u7 - np.unique(_k7, axis=0), axis=1) > 0
_mv7 = _ch7[_i7]; co[_mv7] = _u7[_i7[_mv7]]
print('EYES brow-corner positions smoothed', int(_sp.sum()))
# PF1 (face fix 2026-11-02): Meshy left a small hole (a 4-vertex boundary loop, mirrored to both sides) in the shell beside each cheek at
# the hood edge: the grey "speck" was the background seen through it. Small boundary loops of head + hood (welded by position, up to 6
# vertices, within 1 cm of their centre) are closed by moving their vertices to the loop's centre.
_k4 = np.round(co, 5); _u4, _i4 = np.unique(_k4, axis=0, return_inverse=True); _i4 = _i4.ravel()
_t4 = _i4[tri[np.isin(comp[tri[:, 0]], (kh, names.index('scarf')))]]
_e4 = np.sort(np.vstack([_t4[:, [0, 1]], _t4[:, [1, 2]], _t4[:, [2, 0]]]), axis=1)
_ue, _ce = np.unique(_e4, axis=0, return_counts=True); _bd = _ue[_ce == 1]
from collections import defaultdict as _ddd
_adj = _ddd(list)
for _a, _b in _bd: _adj[_a].append(_b); _adj[_b].append(_a)
_seen = set(); _closed = 0
for _v in list(_adj):
    if _v in _seen: continue
    _st = [_v]; _lp = []
    while _st:
        _x = _st.pop()
        if _x in _seen: continue
        _seen.add(_x); _lp.append(_x); _st += _adj[_x]
    _P = _u4[_lp]
    if len(_lp) <= 6 and np.linalg.norm(_P - _P.mean(0), axis=1).max() < 0.0100:
        _m = np.isin(_i4, _lp); co[_m] = _P.mean(0); _closed += 1
print('HOLES closed', _closed)
# slivers: the bisect left vertices a hair off the plane (|x| 0.2-2 mm) whose mirror twins make needle faces with steep normals along the
# midline (the dark line down the chin). Snapped onto x = 0 they become zero-area faces that add nothing to the normals.
SNAP = 0.0025
for part in ('head', 'scarf', 'dress', 'skirt', 'lining'):
    k = names.index(part); q = (comp == k) & (np.abs(co[:, 0]) < SNAP) & (np.abs(co[:, 0]) > 0)
    co[q, 0] = 0; print('SNAP', part, int(q.sum()))
# nose fix 2026-11-02: the snap leaves fins, faces lying in the x = 0 plane with area (in coincident mirrored pairs). Across a concave
# stretch (the nose's underside, the bridge) a fin stands out of the surface and, lit with the normals of the tip above it, drew as a thin
# light line down the nose in close-ups. Each face fin is made degenerate: its apex (the vertex opposite its longest edge) moves onto
# that edge, staying on the midline (welded positions; at most 3 mm; repeated until none is left).
_k6 = np.round(co, 6); _u6, _i6 = np.unique(_k6, axis=0, return_inverse=True); _i6 = _i6.ravel()
_t6 = np.unique(np.sort(_i6[tri[comp[tri[:, 0]] == kh]], axis=1), axis=0)
_o6 = _u6.copy(); _nf = 0
for _it in range(20):
    _c6 = _u6[_t6]; _on = (np.abs(_c6[:, :, 0]) < 1e-7).all(1)
    _a6 = np.linalg.norm(np.cross(_c6[:, 1] - _c6[:, 0], _c6[:, 2] - _c6[:, 0]), axis=1) / 2
    _fz = _c6.mean(1)[:, 2] - Z0_
    _fins = np.where(_on & (_a6 > 2e-9) & (_c6.mean(1)[:, 1] < -0.05) & (_fz > 1.45) & (_fz < 1.72))[0]
    if not len(_fins): break
    for _f in _fins:
        _v = _t6[_f]; _q = _u6[_v]
        _el = [np.linalg.norm(_q[(j + 1) % 3] - _q[(j + 2) % 3]) for j in range(3)]; j = int(np.argmax(_el))
        _a, _b = _q[(j + 1) % 3], _q[(j + 2) % 3]; _d = _b - _a; _t = np.clip(np.dot(_q[j] - _a, _d) / max(np.dot(_d, _d), 1e-18), 0, 1)
        _tgt = _a + _t * _d
        if np.linalg.norm(_tgt - _o6[_v[j]]) < 0.003: _u6[_v[j]] = _tgt; _nf += 1
print('FINS collapsed', _nf, 'moves, left', len(_fins), 'max mm', round(float(np.linalg.norm(_u6 - _o6, axis=1).max()) * 1000, 2))
_mv6 = (np.linalg.norm(_u6 - _o6, axis=1) > 0)[_i6]; co[_mv6] = _u6[_i6[_mv6]]
D['co'] = co[D['orig']]
# PF1 (face fix 2026-11-02): the clamped ear plates left head faces turned into the skull beside the cheeks, which drew as a grey speck at
# the hood edge. Head faces there whose normal points into the head have their winding reversed (UVs unchanged).
_c = D['co'][D['tri']].mean(1); _n = np.cross(D['co'][D['tri'][:, 1]] - D['co'][D['tri'][:, 0]], D['co'][D['tri'][:, 2]] - D['co'][D['tri'][:, 0]])
_n /= np.maximum(np.linalg.norm(_n, axis=1, keepdims=True), 1e-12)
_o = _c - np.array([0, 0.0, 1.60 + Z0_]); _o[:, 2] *= 0.3; _o /= np.linalg.norm(_o, axis=1, keepdims=True)
_hz = (D['comp'][D['tri'][:, 0]] == kh) & (np.abs(_c[:, 0]) > 0.05) & (np.abs(_c[:, 0]) < 0.068) & (_c[:, 2] - Z0_ > 1.53) & (_c[:, 2] - Z0_ < 1.62) & (_c[:, 1] > -0.07) & (_c[:, 1] < 0.02)
_ks = names.index('scarf')
_hs = (D['comp'][D['tri'][:, 0]] == _ks) & (np.abs(_c[:, 0]) > 0.05) & (np.abs(_c[:, 0]) < 0.070) & (_c[:, 2] - Z0_ > 1.53) & (_c[:, 2] - Z0_ < 1.62) & (_c[:, 1] > -0.07) & (_c[:, 1] < -0.02)
_flip = (_hz | _hs) & ((_n * _o).sum(1) < -0.3)      # the hood's shards beside the cheek too (its inside lies further out)
D['tri'] = D['tri'].copy(); D['tri'][_flip] = D['tri'][_flip][:, ::-1]; print('EAR faces re-wound', int(_flip.sum()))
np.savez(OUT, **D); print('saved', OUT)
