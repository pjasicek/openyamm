#!/usr/bin/env python3
"""A constant small turn of a shoulder away from the body over a whole loop (the sword hand brushes the lifted skirt all through Walking): the upper arm's local rotation per key takes one world rotation about the figure's fore-aft axis, so the loop stays closed and the motion is MM9's. With t0:t1:ramp a flat window with smooth ramps, for one-shots. Args: <in glb> <out glb> <clip:side:deg[:t0:t1:ramp]> ..."""
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
for job in JOBS:
    f_ = job.split(':'); clip, side, amp = f_[0], f_[1], np.radians(float(f_[2])); win = [float(x) for x in f_[3:6]] if len(f_) > 3 else None
    n = names.index(f'Bip01 {side} UpperArm'); pa = m.parent[n]
    an = next(a for a in d['animations'] if a['name'] == clip)
    ch = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
    sm = an['samplers'][ch['sampler']]
    T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
    ax = np.array([0, 0, 1.0]) * (1 if side == 'L' else -1)      # glTF +z forward: + turns the left arm up and out
    out = []
    for t, q in zip(T, Q):
        a = amp
        if win:
            u = min(1.0, max(0.0, min((t - win[0]) / win[2], (win[1] - t) / win[2]))); a = amp * u * u * (3 - 2 * u)
        W = m.world(m.sample(clip, float(t)))
        P = W[pa][:3, :3]; Pn = P / np.linalg.norm(P[0])
        Rn = Pn.T @ rot(ax, a) @ Pn @ qm(q)
        q2 = matrix_quaternion(Rn); out.append(q2 if q2 @ q >= 0 else -q2)
    sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
    print('ARMOUT', job)
g.write(Path(OUT))
