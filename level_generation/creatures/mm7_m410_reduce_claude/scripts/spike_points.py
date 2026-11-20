#!/usr/bin/env python3
"""Helmet spike points for the LOD build: the spike tip and, at four heights along the spike (kept exactly at LOD0,
faces above 1.585 m), the outermost vertex in four directions, so the coarse LODs keep the spike's height and taper
(playbook: thin top features vanish in LOD3 and pull the picking bounds down). Rest-pose Blender coordinates from
work/mesh_in.npz (unchanged spike vertices). -> work/spike_points.json"""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
sv = np.unique(f[(p == 2) & (v[f].mean(1)[:, 2] > 1.585)])
pts = [v[sv[np.argmax(v[sv, 2])]]]
axis = v[sv, :2].mean(0)
for z in (1.595, 1.62, 1.645, 1.67):
    ring = sv[np.abs(v[sv, 2] - z) < 0.006]
    for dvec in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pts.append(v[ring[np.argmax((v[ring, :2] - axis) @ np.array(dvec))]])
pts = np.unique(np.round(np.array(pts), 6), axis=0)
json.dump(pts.tolist(), open('work/spike_points.json', 'w'), indent=1); print('SPIKE POINTS', len(pts), 'tip z', round(float(pts[:, 2].max()), 4))
