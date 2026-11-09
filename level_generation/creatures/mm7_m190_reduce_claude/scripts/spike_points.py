#!/usr/bin/env python3
"""Top-feature points for the LOD build (playbook: thin top features vanish in the coarse LODs and pull the picking bounds
down; MM6 Dwarf helmet spike): on the picked LOD0 (work/mesh_<tag>.npz, vertices labelled by the nearest source vertex's
shell, work/source_pieces.npz) the helmet top spike's tip and, at four heights along it, its outermost vertex in four
directions; on each horn (shells 17/18: the horn tips are the model's top, 1.400 m) the vertices within 1.5 cm of the tip and, in <bands> height bands
(default 3) from the helmet ring up, the outermost and innermost vertex in x, so the horns keep their curve (six bands
with four points each took 50 of LOD3's ~590 triangles and collapsed the helmet shell). Blender rest coordinates (the LOD0 vertices exactly) -> work/spike_points.json. Usage: spike_points.py <tag> [bands]"""
import json, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load(f'work/mesh_{sys.argv[1]}.npz'); v = d['verts']; s = np.load('work/source_pieces.npz')
pc = s['piece'][cKDTree(s['co']).query(v)[1]]
pts = []
sv = np.flatnonzero((pc == 8) & (v[:, 2] > 1.255)); pts.append(v[sv[np.argmax(v[sv, 2])]])
axis = v[sv, :2].mean(0); z0, z1 = v[sv, 2].min(), v[sv, 2].max()
for z in np.linspace(z0 + 0.1 * (z1 - z0), z0 + 0.7 * (z1 - z0), 4):
    ring = sv[np.abs(v[sv, 2] - z) < 0.006]
    for dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if len(ring):
            pts.append(v[ring[np.argmax((v[ring, :2] - axis) @ np.array(dv))]])
for horn in (17, 18):
    hv = np.flatnonzero(pc == horn); tip = v[hv[np.argmax(v[hv, 2])]]
    # the tip and every horn vertex within 1.5 cm of it: with the tip alone, the collapse placed a neighbour 0.8-2.3 mm
    # above it (LOD1/LOD2 taller than LOD0)
    pts += list(v[hv[np.linalg.norm(v[hv] - tip, axis=1) < 0.015]])
    sgn = np.sign(v[hv, 0].mean()); edges = np.linspace(v[hv, 2].min() + 0.02, v[hv, 2].max(), int(sys.argv[2]) + 1 if len(sys.argv) > 2 else 4)
    for a, b in zip(edges[:-1], edges[1:]):
        m = hv[(v[hv, 2] >= a) & (v[hv, 2] < b)]
        if len(m):
            pts += [v[m[np.argmax(sgn * v[m, 0])]], v[m[np.argmin(sgn * v[m, 0])]]]
pts = np.unique(np.array(pts), axis=0)
json.dump(pts.tolist(), open('work/spike_points.json', 'w'), indent=1)
print('SPIKE POINTS', len(pts), 'helmet spike tip z', round(float(v[sv, 2].max()), 4), 'top z', round(float(pts[:, 2].max()), 4))
