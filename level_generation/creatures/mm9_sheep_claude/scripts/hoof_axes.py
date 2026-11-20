#!/usr/bin/env python3
"""Hoof axis on the bind mesh: yaw of the vertical plane that best mirrors the hoof onto itself (+ = toe outward), and
the sole tilt. Args: <body npz from dump_body.py>"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
d = np.load(sys.argv[1]); P = d['P']


def axis(c0, zmax=0.075):
    Q = P[(np.linalg.norm(P[:, :2] - c0[:2], axis=1) < 0.075) & (P[:, 2] < zmax)]
    c = Q.mean(0)
    best = (1e9, 0, 0)
    for th in np.arange(-45, 45.1, 1.0):
        r = np.radians(th); ca, sa = np.cos(r), np.sin(r)
        # rotate by -th so the candidate axis lands on -Y (forward)
        q = Q - c
        q2 = np.c_[q[:, 0] * ca - q[:, 1] * (-sa) * 1 if False else q[:, 0] * ca + q[:, 1] * sa * -1 * -1, -q[:, 0] * sa + q[:, 1] * ca, q[:, 2]]
        for off in np.arange(-0.012, 0.0121, 0.003):
            m = q2 * [-1, 1, 1] + [2 * off, 0, 0]
            e = cKDTree(q2).query(m)[0].mean()
            if e < best[0]:
                best = (e, th, off)
    low = Q[Q[:, 2] < Q[:, 2].min() + 0.014]
    A = np.c_[low[:, 0] - low[:, 0].mean(), low[:, 1] - low[:, 1].mean(), np.ones(len(low))]
    gx, gy, _ = np.linalg.lstsq(A, low[:, 2], rcond=None)[0]
    return {'centroid': c.round(4).tolist(), 'n': len(Q), 'mirror_err': round(best[0], 4), 'yaw_raw': best[1], 'off': best[2],
            'sole_slope_x_deg': round(float(np.degrees(np.arctan(gx))), 1), 'sole_slope_y_deg': round(float(np.degrees(np.arctan(gy))), 1), 'low_n': len(low)}


for k, c in (('FL', (0.134, -0.27)), ('FR', (-0.134, -0.27)), ('HL', (0.145, 0.49)), ('HR', (-0.145, 0.49))):
    print(k, axis(np.array([*c, 0])))
