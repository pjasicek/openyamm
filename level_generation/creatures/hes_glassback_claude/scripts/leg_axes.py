#!/usr/bin/env python3
"""Leg axes from the normalised body: vertices below the belly (z < 0.47) and outside the midline (|x| > 0.2) are
split into the six legs (k-means from the feet seen in the grid views), then centroids per 5 cm band. Args: npy"""
import sys, json
import numpy as np
from scipy.cluster.vq import kmeans2
P = np.load(sys.argv[1])
sel = P[(P[:, 2] < 0.47) & (np.abs(P[:, 0]) > 0.2)]
INIT = np.array([[0.55, -0.97, 0.2], [-0.55, -0.97, 0.2], [0.6, -0.2, 0.2], [-0.6, -0.2, 0.2], [0.6, 0.55, 0.2],
                 [-0.6, 0.55, 0.2]])
w = np.array([1, 1, 0.3])
c, l = kmeans2(sel * w, INIT * w, minit='matrix', iter=30)
names = ['FL', 'FR', 'ML', 'MR', 'HL', 'HR']
out = {}
for k, n in enumerate(names):
    q = sel[l == k]
    rows = []
    for z in np.arange(0.025, 0.47, 0.05):
        s = q[np.abs(q[:, 2] - z) < 0.025]
        if len(s) > 3:
            rows.append([round(float(z), 3)] + s[:, :2].mean(0).round(3).tolist() + np.ptp(s[:, :2], 0).round(2).tolist())
    out[n] = rows
    print(n, len(q))
    for r in rows:
        print('   z %.3f  x %+.3f y %+.3f  w %.2f d %.2f' % tuple(r))
json.dump(out, open('work/leg_axes.json', 'w'), indent=1)
