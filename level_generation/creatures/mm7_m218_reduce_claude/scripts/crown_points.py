#!/usr/bin/env python3
"""Crown-leaf points for the LOD build (replaces the Swordsman's spike_points.py): per sprig side the highest vertex and
the outermost vertex sideways, forwards and backwards of the crown-leaf pieces (kept exactly at LOD0), so the coarse
LODs keep the 1.80 m top (picking bounds) and the sprigs' spread. Rest-pose Blender coordinates from
work/mesh_in.npz. -> work/crown_points.json"""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
cv = np.unique(f[p == 5]); pts = []
for s in (-1, 1):
    side = cv[np.sign(v[cv, 0]) == s]
    pts.append(v[side[np.argmax(v[side, 2])]])
    for axis, sign in ((0, s), (1, 1), (1, -1)):
        pts.append(v[side[np.argmax(sign * v[side, axis])]])
pts = np.unique(np.round(np.array(pts), 6), axis=0)
json.dump(pts.tolist(), open('work/crown_points.json', 'w'), indent=1)
print('CROWN POINTS', len(pts), 'top z', round(float(pts[:, 2].max()), 4))
