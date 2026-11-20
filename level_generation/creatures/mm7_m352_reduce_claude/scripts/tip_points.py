#!/usr/bin/env python3
"""LOD protected points for the m352 thin features (as m302's for its cap tip and beard tip): on the picked LOD0
(work/mesh_<tag>.npz) the top of the head, the lowest point of the long hair at the back (with its 1.5 cm cluster) and
the beard tip (the lowest vertex in front of the chin, with its 1.5 cm cluster) -> work/spike_points.json.
Usage: tip_points.py <tag>"""
import json, sys
import numpy as np
v = np.load(f'work/mesh_{sys.argv[1]}.npz')['verts']
pts = []
def cluster(i, r=0.015):
    return [v[j].tolist() for j in np.flatnonzero(np.linalg.norm(v - v[i], axis=1) < r)]
top = int(np.argmax(v[:, 2])); pts.append(v[top].tolist())
hb = np.flatnonzero((v[:, 1] > 0.06) & (np.abs(v[:, 0]) < 0.12) & (v[:, 2] > 1.2) & (v[:, 2] < 1.45))
hair = hb[np.argmin(v[hb, 2])]; pts += cluster(hair)
bz = np.flatnonzero((np.abs(v[:, 0]) < 0.04) & (v[:, 1] < -0.06) & (v[:, 2] > 1.40) & (v[:, 2] < 1.52))
btip = bz[np.argmin(v[bz, 2])]; pts += cluster(btip)
json.dump(pts, open('work/spike_points.json', 'w'), indent=1)
print('TIPS top', np.round(v[top], 3), 'hair tip', np.round(v[hair], 3), 'beard tip', np.round(v[btip], 3), 'points', len(pts))
