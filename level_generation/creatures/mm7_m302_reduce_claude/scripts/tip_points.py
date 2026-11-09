#!/usr/bin/env python3
"""LOD protected points for the m302 thin features (as m190's spike_points.py for the helmet spike and horns): on the
picked LOD0 (work/mesh_<tag>.npz) the cap's back tip (the vertex farthest behind the head above 1.15 m) and every vertex
within 1.5 cm of it, the top of the cap, and the beard tip (the lowest beard vertex in front of the chest) with its
1.5 cm cluster -> work/spike_points.json. Usage: tip_points.py <tag>"""
import json, sys
import numpy as np
v = np.load(f'work/mesh_{sys.argv[1]}.npz')['verts']
pts = []
def cluster(i, r=0.015):
    return [v[j].tolist() for j in np.flatnonzero(np.linalg.norm(v - v[i], axis=1) < r)]
hi = np.flatnonzero(v[:, 2] > 1.15)
tip = hi[np.argmax(v[hi, 1])]; pts += cluster(tip)
pts.append(v[np.argmax(v[:, 2])].tolist())
bz = np.flatnonzero((np.abs(v[:, 0]) < 0.08) & (v[:, 1] < -0.15) & (v[:, 2] > 0.7) & (v[:, 2] < 1.0))
btip = bz[np.argmin(v[bz, 2])]; pts += cluster(btip)
json.dump(pts, open('work/spike_points.json', 'w'), indent=1)
print('TIPS cap tip', np.round(v[tip], 3), 'top', np.round(v[np.argmax(v[:, 2])], 3), 'beard tip', np.round(v[btip], 3), 'points', len(pts))
