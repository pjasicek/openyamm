#!/usr/bin/env python3
"""Leg axes of the normalised body (work/body_norm.npy: vertices in metres, forward -Y, up +Z): per foot, climb in
2 cm slices taking the vertices near the previous centroid; prints the centroid chain per leg."""
import sys
import numpy as np
from scipy.cluster.vq import kmeans2
P = np.load(sys.argv[1])
low = P[P[:, 2] < 0.05]
INIT = np.array([[0.55, -0.95], [-0.55, -0.95], [0.55, -0.21], [-0.55, -0.21], [0.6, 0.54], [-0.6, 0.54]])
c, l = kmeans2(low[:, :2], INIT, minit='matrix')
legs = {}
order = np.argsort(c[:, 1])
for rank, k in enumerate(order):
    name = 'FMH'[rank // 2] + ('L' if c[k, 0] > 0 else 'R')
    legs[name] = c[k]
    print('FOOT', name, c[k].round(3))
for name in sorted(legs):
    cxy = legs[name].copy(); chain = []
    for z in np.arange(0.02, 0.8, 0.06):
        s = P[(np.abs(P[:, 2] - z) < 0.02) & (np.linalg.norm(P[:, :2] - cxy, axis=1) < 0.14)]
        if len(s) < 5:
            break
        cxy = s[:, :2].mean(0)
        spread = np.ptp(s[:, :2], axis=0)
        chain.append((round(z, 2), cxy.round(3), spread.round(2), len(s)))
    print(name)
    for row in chain:
        print('  ', row)
