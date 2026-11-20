#!/usr/bin/env python3
"""Top points for the LOD build (playbook: thin top features vanish in the coarse LODs and pull the picking bounds
down): the crown's highest vertex and its highest vertex in every 15-degree sector about its axis (the crown rim is
the model's top, 1.700 m = 258.9 units at the binding scale 152.29), and each horn's tip (highest vertex) and its
outermost vertex. Rest-pose Blender coordinates from work/mesh_in.npz (crown and horns are kept exactly at LOD0).
-> work/spike_points.json"""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
cv = np.unique(f[p == 5]); ax = v[cv, :2].mean(0)
az = np.degrees(np.arctan2(v[cv, 1] - ax[1], v[cv, 0] - ax[0])) % 360
pts = [v[cv[np.argmax(v[cv, 2])]]]
for a0 in range(0, 360, 15):
    m = (az >= a0) & (az < a0 + 15)
    if m.any():
        pts.append(v[cv[m][np.argmax(v[cv[m], 2])]])
hv = np.unique(f[p == 9])
for s in (-1, 1):
    m = hv[s * v[hv, 0] > 0]
    pts.append(v[m[np.argmax(v[m, 2])]]); pts.append(v[m[np.argmax(s * v[m, 0])]])
pts = np.unique(np.round(np.array(pts), 6), axis=0)
json.dump(pts.tolist(), open('work/spike_points.json', 'w'), indent=1)
print('SPIKE POINTS', len(pts), 'crown top z', round(float(v[cv, 2].max()), 4), 'horn tips z',
      [round(float(v[hv[s * v[hv, 0] > 0], 2].max()), 4) for s in (-1, 1)])
