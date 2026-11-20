#!/usr/bin/env python3
"""Chin and jaw smoothed (PF3 second pass, 2026-11-02; orchestrator: "a hard-edged lighter block on the chin/jaw", "a pixelated block under
the chin"). A grey-clay render with and without the normal map showed it is geometry: a crease running from the lower lip's corner down to the
chin's underside left by F1's mouth-cavity closure and fin collapse. Head-shell positions below the lower lip (1.47-1.545 m over the soles,
|x| < 6 cm, in front of the neck) are Laplacian-smoothed over the mesh welded by asm vertex (positions only, UVs unchanged), moves capped at
CAP and eased out at the zone's edge; the lips above 1.545 m are held. Rows sharing an asm vertex move together.
Args: <uv_tex2 npz in> <out npz> [passes] [cap m]"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); PASSES = int(sys.argv[3]) if len(sys.argv) > 3 else 12; CAP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.003
co, tri, orig, comp = D['co'], D['tri'], D['orig'], D['comp']; names = [str(x) for x in D['names']]; Z0 = -0.9297
# ---- pass 4 (orchestrator: "a white zigzag streak on the cheek in front of the ear", profile view; F1 has the same): its cause is the
# small hole Meshy left beside each cheek (4-vertex rim, ~1 cm wide, |x| 6.2 cm, 1.59 m), which tweak_pf1.py closed by collapsing the rim
# onto its centre: the faces round that point fold into two thin wedges that a light from the side draws as a bright "<". Here the rim
# vertices are put back on a small ring (half their original spread round the centre, on the cheek's plane) and the hole is capped with two
# triangles (head material, the rim rows' own UVs: skin texels).
_A = np.load(str(__import__('pathlib').Path(sys.argv[1]).parent / 'asm_frozen.npz')); _kh = names.index('head')
_k6 = np.round(co, 6); _grp = {}
for _i in np.where(comp == _kh)[0]: _grp.setdefault(tuple(_k6[_i]), {}).setdefault(int(orig[_i]), []).append(_i)
_caps = []
for _key, _ov in _grp.items():
    if len(_ov) < 3 or len(_ov) > 6 or abs(_key[0]) < 0.05 or not (1.57 < _key[2] - Z0 < 1.61): continue
    _c = np.array(_key); _os = sorted(_ov); _src = _A['co'][_os]; _d = _src - _src.mean(0)
    _n = np.linalg.svd(_d)[2][2]; _n *= np.sign(_n[0] * np.sign(_c[0]))           # outward
    _d = _d - np.outer(_d @ _n, _n); _new = _c + 0.5 * _d
    _e1 = _d[0] / np.linalg.norm(_d[0]); _e2 = np.cross(_n, _e1); _ang = np.arctan2(_d @ _e2, _d @ _e1); _ordr = np.argsort(_ang)
    for _j, _o in enumerate(_os):
        for _r in _ov[_o]: co[_r] = _new[_j]
    _rows = [_ov[_os[j]][0] for j in _ordr]
    for _t in ((_rows[0], _rows[1], _rows[2]), (_rows[0], _rows[2], _rows[3])) if len(_rows) == 4 else [(_rows[0], _rows[j], _rows[j + 1]) for j in range(1, len(_rows) - 1)]:
        _fn = np.cross(co[_t[1]] - co[_t[0]], co[_t[2]] - co[_t[0]])
        _caps.append(_t if _fn @ _n > 0 else (_t[0], _t[2], _t[1]))
if _caps:
    # the rim rows lie in different UV islands, so a cap on their UVs stretched over the atlas (a white sliver): the cap gets its own rows,
    # every corner on the UV of its first rim row (one skin texel)
    _caps = np.array(_caps); _new_rows = []
    for _ci, _t in enumerate(_caps):
        for _k in range(3):
            _new_rows.append(_t[_k]); _caps[_ci, _k] = len(co) + len(_new_rows) - 1
    _nr = np.array(_new_rows); _uv0 = D['uv'][np.array([r for r in _nr[::3] for _ in range(3)])]
    for _key2 in ('co', 'orig', 'comp'): D[_key2] = np.concatenate([D[_key2], D[_key2][_nr]])
    D['uv'] = np.vstack([D['uv'], _uv0]); co, orig, comp = D['co'], D['orig'], D['comp']
    D['tri'] = np.vstack([D['tri'], np.array(_caps)]); D['mat'] = np.r_[D['mat'], np.ones(len(_caps), D['mat'].dtype)]
    D['inner'] = np.r_[D['inner'], np.zeros(len(_caps), bool)]; tri = D['tri']
print('HOLE caps', len(_caps))
kh = names.index('head')
ov, inv = np.unique(orig, return_inverse=True)
P = np.zeros((len(ov), 3)); P[inv] = co
isH = np.zeros(len(ov), bool); isH[inv[comp == kh]] = True
T = inv[tri]; e = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)
zs = P[:, 2] - Z0
def ss(v, a, b):
    t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
# pass 3 (user: "giga strange face geometry, check the profile"): the smoothing is limited to the lip-corner crease between the chin point and
# the lower lip (1.518-1.546 m, |x| < 4.5 cm); pass 2's smoothing down to 1.47 m rounded the under-chin into the neck
w = isH * ss(zs, 1.512, 1.520) * (1 - ss(zs, 1.538, 1.546)) * (1 - ss(np.abs(P[:, 0]), 0.040, 0.048)) * (1 - ss(P[:, 1], -0.050, -0.035))
# vertices shared with other parts (seams) stay
shared = np.zeros(len(ov), bool)
for c in np.unique(comp):
    if c != kh:
        shared[np.unique(inv[comp == c])] &= True
        m = np.zeros(len(ov), bool); m[inv[comp == c]] = True; shared |= m & isH
# pass 2: the clamped ear plates beside each cheek (a flat facet at an angle to the cheek: a darker block in lit side views) smoothed into
# the cheek the same way
w = np.maximum(w, isH * ss(np.abs(P[:, 0]), 0.046, 0.054) * ss(zs, 1.52, 1.535) * (1 - ss(zs, 1.615, 1.63)) * ss(P[:, 1], -0.085, -0.07) * (1 - ss(P[:, 1], 0.005, 0.02)))
# head vertices near the hood's interleaved faces stay put (moved, they bared the white hood faces behind them as a zigzag)
from scipy.spatial import cKDTree as _K
_sc = np.zeros(len(ov), bool); _sc[inv[comp == names.index('scarf')]] = True
_d, _ = _K(P[_sc & ~isH]).query(P)
w *= ss(_d, 0.004, 0.009)
# part seams are coincident but distinct vertices (the split Meshy shell): held by position too
from scipy.spatial import cKDTree as _K0
_nh = np.zeros(len(ov), bool); _nh[inv[comp != kh]] = True
_dd, _ = _K0(P[_nh]).query(P); shared |= isH & (_dd < 1e-5)
w[shared] = 0
P0 = P.copy()
for _ in range(PASSES):
    acc = np.zeros_like(P); deg = np.zeros(len(P))
    np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
    L = acc / np.maximum(deg, 1)[:, None]
    P = P + (L - P) * 0.5 * w[:, None]
    d = P - P0; n = np.linalg.norm(d, axis=1, keepdims=True); P = P0 + d * np.minimum(1, CAP / np.maximum(n, 1e-12))
    P[np.abs(P0[:, 0]) < 1e-6, 0] = 0                    # the midline stays on x = 0
# ---- pass 3: chin and jaw line sculpted (young woman, MM9 F3's profile: chin almost under the lips, a flat under-chin meeting the neck at
# an angle). F1's soft older chin receded 1.5 cm behind the lips and the under-chin rounded into the neck (a "double chin" slab in profile).
# (a) the chin point forward and down: a bump round (x 0, 1.515 m) on the face's front, up to CHIN_FWD forward and CHIN_DOWN down;
# (b) the corner between under-chin and neck carved: per |x| an ideal corner (y_c, z_c) (front of the neck, the under-chin plane), every
#     head vertex in front of the neck line and below the under-chin plane (the rounded bulge) moves to the nearer of the two (capped at
#     CARVE_MAX), eased out toward the ears; (c) two light smoothing passes over the moved zone (holding the corner line).
CHIN_FWD, CHIN_DOWN, CARVE_MAX, SULCUS = 0.012, 0.004, 0.014, 0.0025
held = shared.copy()
ax = np.abs(P[:, 0])
bump = isH * np.exp(-0.5 * ((P[:, 0] / 0.025) ** 2 + ((zs - 1.525) / 0.011) ** 2)) * ss(-P[:, 1], 0.065, 0.100) * ~held
P[:, 1] -= CHIN_FWD * bump; P[:, 2] -= CHIN_DOWN * bump
sul = isH * np.exp(-0.5 * ((P[:, 0] / 0.016) ** 2 + ((zs - 1.537) / 0.0045) ** 2)) * ss(-P[:, 1], 0.09, 0.105) * ~held      # the mentolabial fold
P[:, 1] += SULCUS * sul
zs = P[:, 2] - Z0
yc = -0.047 + 0.017 * np.clip(ax / 0.045, 0, 1.25) ** 2
zc = 1.505 + 0.023 * np.clip(ax / 0.045, 0, 1.25) ** 2
dy = yc - P[:, 1]; dz = zc - zs
zone = isH & ~held & (dy > 0) & (dz > 0) & (zs > zc - 0.055) & (P[:, 1] > -0.115) & (ax < 0.058)
fade = (1 - ss(ax, 0.045, 0.058))
mv = np.zeros(len(P)); P2 = P.copy()
up = zone & (dz <= dy); bk = zone & (dz > dy)
P2[up, 2] += np.minimum(dz[up], CARVE_MAX) * fade[up]; P2[bk, 1] += np.minimum(dy[bk], CARVE_MAX) * fade[bk]
carved = np.linalg.norm(P2 - P, axis=1); P = P2
zone2 = np.zeros(len(P), bool); zone2[np.unique(e[np.isin(e, np.where(carved > 1e-5)[0]).any(1)])] = True; zone2 &= isH & ~held
for _ in range(2):
    acc = np.zeros_like(P); deg = np.zeros(len(P))
    np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
    P[zone2] = P[zone2] + (acc[zone2] / np.maximum(deg[zone2], 1)[:, None] - P[zone2]) * 0.3
P[np.abs(P0[:, 0]) < 1e-6, 0] = 0
print('CHIN pass3: bump', int((bump > 0.05).sum()), 'carved', int((carved > 1e-5).sum()), 'max mm', round(float(carved.max()) * 1000, 1))
# ---- pass 3: the nose tip rounded (it drooped into a point in profile): head vertices within 9 mm of the tip, Laplacian-smoothed (6 passes,
# at most 2.5 mm) and lifted up to 1.5 mm, eased out
fr = isH & (np.abs(P[:, 0]) < 0.006) & (zs > 1.555) & (zs < 1.61)
tip = P[np.where(fr)[0][np.argmin(P[fr, 1])]]
dtip = np.linalg.norm(P - tip, axis=1); wn = isH * ~held * (1 - ss(dtip, 0.005, 0.009)); Pn0 = P.copy()
for _ in range(6):
    acc = np.zeros_like(P); deg = np.zeros(len(P))
    np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
    P = P + (acc / np.maximum(deg, 1)[:, None] - P) * 0.5 * wn[:, None]
    d_ = P - Pn0; n_ = np.linalg.norm(d_, axis=1, keepdims=True); P = Pn0 + d_ * np.minimum(1, 0.0025 / np.maximum(n_, 1e-12))
P[:, 2] += 0.0015 * wn * (1 - ss(P[:, 2] - tip[2], -0.004, 0.004))
P[np.abs(P0[:, 0]) < 1e-6, 0] = 0
print('NOSE tip at', np.round(tip, 3).tolist(), 'rounded', int((wn > 0.05).sum()))
# ---- pass 4 (orchestrator: "a white zigzag streak on the cheek in front of the ear"): tweak_pf1.py's ear clamp (|x| <= 6.3 cm) leaves a
# folded ridge where the clamped plane meets the cheek (46-49 deg edges at x 6.3 cm, 1.57-1.59 m), which a light from the side draws as a
# bright "<"; the 4-vertex hole tweak_pf1.py closed by collapsing it (zero-area faces at x 6.1 cm, y -5.5 cm, 1.589 m) sits in it.
# F1 has the same. Head vertices of that zone are smoothed (16 passes, at most 4 mm) and every coincident vertex of another part
# (the hood twins at the seam) takes the same move, so the seam stays shut.
zr = isH & (np.abs(P[:, 0]) > 0.048) & ((P[:, 2] - Z0) > 1.555) & ((P[:, 2] - Z0) < 1.620) & (P[:, 1] > -0.080) & (P[:, 1] < -0.005)
wr = zr * (1 - ss(np.abs((P[:, 2] - Z0) - 1.588), 0.022, 0.032)) * ss(np.abs(P[:, 0]), 0.048, 0.054) * (1 - ss(-P[:, 1], 0.070, 0.080))
# hood faces interleave with the head at the hood's rim: head vertices within a few mm of a hood vertex (not its seam twin) stay put, else
# the smoothing folds a sliver against the hood (a white shard at the rim)
_hsc = np.zeros(len(P), bool); _hsc[inv[comp == names.index('scarf')]] = True
_dsc, _ = _K0(P[_hsc]).query(P, k=2); _dn = np.where(_dsc[:, 0] < 1e-5, _dsc[:, 1], _dsc[:, 0])
# (tried: holding head vertices within 1-8 mm of hood vertices; that left the fold, so none are held)
# wr = wr * ss(_dn, 0.0012, 0.0035)
Pr0 = P.copy()
for _ in range(30):
    acc = np.zeros_like(P); deg = np.zeros(len(P))
    np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
    P = P + (acc / np.maximum(deg, 1)[:, None] - P) * 0.5 * wr[:, None]
    d_ = P - Pr0; n_ = np.linalg.norm(d_, axis=1, keepdims=True); P = Pr0 + d_ * np.minimum(1, 0.005 / np.maximum(n_, 1e-12))
mvr = P - Pr0; movedr = np.linalg.norm(mvr, axis=1) > 1e-7
_kk = {tuple(np.round(Pr0[i], 5)): i for i in np.where(movedr)[0]}
for i in np.where(~isH)[0]:
    k = tuple(np.round(Pr0[i], 5))
    if k in _kk: P[i] = Pr0[i] + mvr[_kk[k]]
print('EAR ridge smoothed', int(movedr.sum()), 'max mm', round(float(np.linalg.norm(mvr, axis=1).max()) * 1000, 2))
# pass 2: the hood's lower back (and the neck seam it shares) tucked 8 mm in under the veil, so its rim cannot poke out over the veil
# when the head turns (the ledge across the back in walk and talk); all of it lies under the veil (behind the ears, 1.48-1.60 m)
isS = np.zeros(len(ov), bool); isS[inv[comp == names.index('scarf')]] = True
_nd = np.zeros(len(ov), bool); _nd[inv[comp == names.index('dress')]] = True
_dd2, _ = _K0(P[_nd]).query(P)
wt = (isH | isS) * ss(P[:, 1], -0.005, 0.03) * (1 - ss(zs, 1.585, 1.605)) * ss(zs, 1.47, 1.50) * ss(_dd2, 0.0005, 0.012)      # pass 3: the head/dress seam at the nape stays shut
r = np.hypot(P[:, 0], P[:, 1] - 0.0); dirv = np.c_[P[:, 0], P[:, 1], np.zeros(len(P))] / np.maximum(r, 1e-6)[:, None]
P = P - dirv * (0.008 * wt)[:, None]
print('HOOD tucked', int((wt > 0.01).sum()), 'vertices')
# pass 4: positions that coincided before this script (tweak_pf1.py closes Meshy's small holes by collapsing their rims onto one point;
# mirrored midline pairs) stay coincident: each such group takes its mean position. Smoothed separately, the collapsed hole beside each ear
# reopened and showed the white veil lining through it (the sliver at the braid's top).
_k0 = np.round(P0, 6); _ug, _gi = np.unique(_k0, axis=0, return_inverse=True); _gi = _gi.ravel()
_cnt = np.bincount(_gi); _sum = np.zeros((len(_ug), 3)); np.add.at(_sum, _gi, P)
_multi = _cnt[_gi] > 1; P[_multi] = (_sum / _cnt[:, None])[_gi[_multi]]
print('COINCIDENT groups kept shut', int((_cnt > 1).sum()))
D['co'] = P[inv]
np.savez(sys.argv[2], **D)
mv = np.linalg.norm(P - P0, axis=1); print('CHIN smoothed', int((mv > 1e-5).sum()), 'vertices, max mm', round(float(mv.max()) * 1000, 2))
