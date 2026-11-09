#!/usr/bin/env python3
"""Horn points for the LOD build (playbook: thin top features vanish in the coarse LODs and pull the picking bounds
down): on the picked LOD0 (work/mesh_<tag>.npz) the horn vertices (nearest source vertex on a horn face,
work/horns.npy from m286_pieces.py), per horn the vertices within 1.5 cm of its tip (the model's top; with the tip
alone the collapse places a neighbour above it) and, in <bands> height bands (default 3) from the horn root up, the
outermost and innermost vertex in x, so the horns keep their curve in LOD2/LOD3.
Blender rest coordinates (the LOD0 vertices exactly) -> work/spike_points.json. Usage: spike_points.py <tag> [bands]"""
import json, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load(f'work/mesh_{sys.argv[1]}.npz'); v = d['verts']; s = np.load('work/mesh_in.npz')
hv_src = np.zeros(len(s['verts']), bool); hv_src[np.unique(s['faces'][np.load('work/horns.npy')])] = True
dist, near = cKDTree(s['verts']).query(v)
horn = hv_src[near] & (dist < 0.01)
pts = []
for sgn in (-1, 1):
    hv = np.flatnonzero(horn & (np.sign(v[:, 0]) == sgn)); tip = v[hv[np.argmax(v[hv, 2])]]
    pts += list(v[hv[np.linalg.norm(v[hv] - tip, axis=1) < 0.015]])
    edges = np.linspace(v[hv, 2].min() + 0.02, v[hv, 2].max(), int(sys.argv[2]) + 1 if len(sys.argv) > 2 else 4)
    for a, b in zip(edges[:-1], edges[1:]):
        m = hv[(v[hv, 2] >= a) & (v[hv, 2] < b)]
        if len(m):
            pts += [v[m[np.argmax(sgn * v[m, 0])]], v[m[np.argmin(sgn * v[m, 0])]]]
pts = np.unique(np.array(pts), axis=0)
json.dump(pts.tolist(), open('work/spike_points.json', 'w'), indent=1)
print('SPIKE POINTS', len(pts), 'horn vertices', int(horn.sum()), 'top z', round(float(pts[:, 2].max()), 4), 'model top', round(float(v[:, 2].max()), 4))
