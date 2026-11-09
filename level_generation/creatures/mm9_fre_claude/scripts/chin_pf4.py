#!/usr/bin/env python3
"""PF4 chin and jaw (2026-11-02): PeasantF3's chin_smooth_pf3.py (its pass 3, user-reviewed: F1's soft chin recedes 1.5 cm behind the lips
and the under-chin rounds into the neck, a "swollen under-chin" in profile) applied to the same F1 head: the lip-corner crease smoothed, the
chin point 12 mm forward and 4 mm down, a 2.5 mm mentolabial fold, the under-chin/neck corner carved. MM9 F4's chin sits 1.2 cm further
forward than ours (sections), so the same sculpt. Not carried over (they belong to F1's hood, now under PF4's new hood): the hole caps
beside the cheeks, the ear-plate and ear-ridge smoothing, the hood tuck; the nose is left as F1's (no smoothing of Meshy's nose).
Positions only, UVs unchanged; coincident positions stay coincident. Args: <uv_tex2 npz in> <out npz> [passes] [cap m]"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); PASSES = int(sys.argv[3]) if len(sys.argv) > 3 else 12; CAP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.003
co, tri, orig, comp = D['co'], D['tri'], D['orig'], D['comp']; names = [str(x) for x in D['names']]; Z0 = -0.9297
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
