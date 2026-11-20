#!/usr/bin/env python3
"""The fringe's centre tip hung onto the forehead (z 0.931, 2 cm proud of the skin; user, 2026-11-01: "a dark hair tip pokes
onto the forehead"). Fringe vertices (comp 4) are folded up towards the hairline: z' = TOP - (TOP - z) * k, k = 0.55 at the
centre easing to 1 at |x| 0.06, and pulled back towards the skin by the same share. Vertex moves only (UVs, weights kept).
Args: <in npz> <out npz>"""
import sys, numpy as np
D = dict(np.load(sys.argv[1])); co = D['co'].copy(); comp = D['comp']
TOP = 1.02
f = comp == 4
ax = np.abs(co[f, 0]); t = np.clip(ax / 0.06, 0, 1); t = t * t * (3 - 2 * t)
k = 0.55 + 0.45 * t
z0 = co[f, 2].copy()
co[f, 2] = TOP - (TOP - z0) * k
lift = co[f, 2] - z0
co[f, 1] = co[f, 1] + np.clip(-0.022 - co[f, 1], 0, None) * np.clip(lift / 0.04, 0, 1) * 0.0 + np.where(co[f, 1] < -0.02, (-0.02 - co[f, 1]) * (1 - k) * 0.8, 0)
D['co'] = co
# the folded tip's remnant hung under the arch as a small block (coordinator, 2026-11-01: "dark brown rectangular stub"):
# the centre fringe faces below z 0.99 are removed
tri = D['tri']; ct = co[tri].mean(1)
drop = (comp[tri[:, 0]] == 4) & (np.abs(ct[:, 0]) < 0.016) & (ct[:, 2] < 0.99)
# and the hair shell's own tongue under the arch (the block still read after the fringe stub went): forehead skin lies under it
drop |= (comp[tri[:, 0]] == 1) & (np.abs(ct[:, 0]) < 0.022) & (ct[:, 2] < 0.978) & (ct[:, 1] < 0.005)
keep = ~drop; D['tri'] = tri[keep]; D['mat'] = D['mat'][keep]
print('FRINGE stub faces removed', int(drop.sum()))
np.savez(sys.argv[2], **D)
print('FRINGE lifted', int(f.sum()), 'verts; centre low z', round(float(co[f][np.abs(co[f, 0]) < 0.02][:, 2].min()), 3))
