#!/usr/bin/env python3
"""Fre pass 2: specks at the chin point, under the lower lip and beside the nose are tiny head faces (collapsed slivers, a fraction of a
millimetre) whose UVs point at a texel unlike the skin round them. Every head-shell face of 3D area < AMAX m^2 (or zero UV area) gets three
new rows on the UV centroid of the nearest head face of normal size (3D centroid distance), so it shows the colour of the surface it
lies on. Positions and every other row unchanged. Args: <uv npz in> <uv npz out> [AMAX]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
D = dict(np.load(sys.argv[1])); AMAX = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5e-6
co, tri, uv, mat, comp = D['co'], D['tri'].copy(), D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
H = np.where((mat == 1) & (comp[tri[:, 0]] == names.index('head')))[0]
a3 = 0.5 * np.linalg.norm(np.cross(co[tri[H, 1]] - co[tri[H, 0]], co[tri[H, 2]] - co[tri[H, 0]]), axis=1)
T = uv[tri[H]]; a2 = 0.5 * np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 2, 0] - T[:, 0, 0]) * (T[:, 1, 1] - T[:, 0, 1]))
tiny = (a3 < AMAX) | (a2 < 1e-12); big = ~tiny
c3 = co[tri[H]].mean(1); kd = cKDTree(c3[big]); _, j = kd.query(c3[tiny]); src = H[big][j]
newuv = uv[tri[src]].mean(1)
add_co, add_uv, add_orig, add_comp = [], [], [], []; n0 = len(co)
for k, f in enumerate(H[tiny]):
    rows = []
    for r in tri[f]:
        add_co.append(co[r]); add_uv.append(newuv[k]); add_orig.append(D['orig'][r]); add_comp.append(comp[r]); rows.append(n0 + len(add_co) - 1)
    tri[f] = rows
D['co'] = np.vstack([co, add_co]); D['uv'] = np.vstack([uv, add_uv]); D['orig'] = np.r_[D['orig'], add_orig]; D['comp'] = np.r_[comp, add_comp]; D['tri'] = tri
np.savez(sys.argv[2], **D); print('TINY head faces remapped', int(tiny.sum()))
