#!/usr/bin/env python3
"""A constant small abduction of a shoulder over every clip: MM9's bind holds the right arm a little closer than its left and our doublet is fuller at the hip, so the hand rests inside the skirt in Standing. One constant world rotation about the figure's fore-aft axis in the parent's frame,
the same at every key, so it cannot add jitter. Args: <in glb> <out glb> <side:deg> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT, *JOBS = sys.argv[1:]
g = Glb(Path(IN)); d = g.json; m = Model(g)
names = [n.get('name') for n in d['nodes']]
def rot(ax, a):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def qm(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
n0 = {}
for job in JOBS:
    side, amp = job.split(':'); amp = np.radians(float(amp))
    n = names.index(f'Bip01 {side} UpperArm'); pa = m.parent[n]
    W0 = m.world({})
    ax0 = np.array([0, 0, 1.0]) * (1 if side == 'L' else -1)
    for an in d['animations']:
        clip = an['name']
        ch = next((c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation'), None)
        if ch is None: continue
        sm = an['samplers'][ch['sampler']]
        T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
        out = []
        for t, q in zip(T, Q):
            P = W0[pa][:3, :3]; Pn = P / np.linalg.norm(P[0])       # the figure's axis at rest, in the clavicle's frame: the offset travels with the shoulder
            Rn = Pn.T @ rot(ax0, amp) @ Pn @ qm(q)
            q2 = matrix_quaternion(Rn); out.append(q2 if q2 @ q >= 0 else -q2)
        sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
    print('ARMCONST', job)
g.write(Path(OUT))
