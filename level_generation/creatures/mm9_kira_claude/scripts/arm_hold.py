#!/usr/bin/env python3
"""A shoulder offset held from a clip's first key and faded out before its fast part (a hand resting on the hip as the clip starts:
Njam_Spell1). Constant in the clavicle's frame until T_HOLD, smoothstep to zero by T_END, then MM9's motion untouched: a constant over
the whole clip turned the fast throw by the offset (jitter gate: 1.85 deg/f over MM9). Args: <in glb> <out glb> <clip:side:t_hold:t_end:deg> ..."""
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
W0 = m.world({})
for job in JOBS:
    clip, side, th, te, amp = job.split(':'); th, te, amp = float(th), float(te), np.radians(float(amp))
    n = names.index(f'Bip01 {side} UpperArm'); pa = m.parent[n]
    an = next(a for a in d['animations'] if a['name'] == clip)
    ch = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
    sm = an['samplers'][ch['sampler']]
    T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
    ax0 = np.array([0, 0, 1.0]) * (1 if side == 'L' else -1)
    P = W0[pa][:3, :3]; Pn = P / np.linalg.norm(P[0])
    out = []
    for t, q in zip(T, Q):
        u = np.clip((t - th) / (te - th), 0, 1); k = 1 - u * u * (3 - 2 * u)
        Rn = Pn.T @ rot(ax0, amp * k) @ Pn @ qm(q)
        q2 = matrix_quaternion(Rn); out.append(q2 if q2 @ q >= 0 else -q2)
    sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
    print('ARMHOLD', job)
g.write(Path(OUT))
