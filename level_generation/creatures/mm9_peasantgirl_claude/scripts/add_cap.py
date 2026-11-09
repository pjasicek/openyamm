#!/usr/bin/env python3
"""Waist cap (see-through gate, 2026-11-02: from the feet of the corpse, and level with a falling body, the view up the skirt met the inside of
the bodice, whose one-sided cloth the game culls: 1477 background pixels). A disc across the inside of the dress at the waist, facing
down (into the skirt), its rim 1.5 mm inside the skirt lining (6 mm left a sliver from below); new faces only, so every existing UV and the paid paints stay valid.
UVs: one dark lining texel (the lining's darkest vertex UV). Weights: each new vertex takes the original index (`orig`) of the nearest
skirt/lining vertex at that height, the centre the nearest at the axis. Part 'lining' (material 0). Args: <in uv npz> <out uv npz> [z (MM9 frame)]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
D = dict(np.load(sys.argv[1])); co, tri, uv, orig, mat, comp = D['co'], D['tri'], D['uv'], D['orig'], D['mat'], D['comp']
names = [str(x) for x in D['names']]; ZC = float(sys.argv[3]) if len(sys.argv) > 3 else 0.235
sk = np.isin(comp, [names.index('skirt'), names.index('lining')])
band = sk & (np.abs(co[:, 2] - ZC) < 0.02)
c0 = co[band].mean(0); c0[2] = ZC
NA = 32; rad = np.zeros(NA); rel = co[band] - c0; ph = np.arctan2(rel[:, 1], rel[:, 0]); rr = np.hypot(rel[:, 0], rel[:, 1])
for i in range(NA):
    a = 2 * np.pi * i / NA; d = np.abs((ph - a + np.pi) % (2 * np.pi) - np.pi); s = d < 2 * np.pi / NA * 1.5
    rad[i] = rr[s].min() if s.any() else rr.min()                  # the innermost wall (the lining) at this angle
for _ in range(2): rad = 0.5 * rad + 0.25 * (np.roll(rad, 1) + np.roll(rad, -1))
rad = np.maximum(rad - 0.0015, 0.01)
P = [c0] + [c0 + np.array([np.cos(2 * np.pi * i / NA) * rad[i], np.sin(2 * np.pi * i / NA) * rad[i], 0.0]) for i in range(NA)]
P = np.array(P)
lin = np.where(comp == names.index('lining'))[0]
# the darkest lining texel would need the image; the lining is darkened uniformly in tiers_pg.py, so any lining vertex UV is a lining texel
u0 = uv[lin[np.argmin(np.abs(co[lin, 2] - ZC))]]
kd = cKDTree(co[sk]); _, nn = kd.query(P); og = orig[np.where(sk)[0][nn]]
n0 = len(co); T = [[n0, n0 + 1 + (i + 1) % NA, n0 + 1 + i] for i in range(NA)]      # facing down (-z)
fn = np.cross(P[T[0][1] - n0] - P[0], P[T[0][2] - n0] - P[0])
if fn[2] > 0: T = [[a, c, b] for a, b, c in T]
D['co'] = np.vstack([co, P]); D['uv'] = np.vstack([uv, np.repeat(u0[None], len(P), 0)]); D['orig'] = np.concatenate([orig, og])
D['comp'] = np.concatenate([comp, np.full(len(P), names.index('lining'))]); D['tri'] = np.vstack([tri, np.array(T)])
D['mat'] = np.concatenate([mat, np.zeros(len(T), mat.dtype)])
if 'inner' in D: D['inner'] = np.concatenate([D['inner'], np.ones(len(T), bool)])
np.savez(sys.argv[2], **D); print('CAP waist z', ZC, 'radius', rad.min().round(3), rad.max().round(3), 'faces', len(T))
