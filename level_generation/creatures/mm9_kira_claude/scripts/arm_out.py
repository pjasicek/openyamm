#!/usr/bin/env python3
"""One raised-cosine bump of a shoulder, away from the body (a hand passing through the hip in a clip): the upper arm's local rotation per key takes a world rotation about the figure's fore-aft axis, amplitude AMP deg, window T0..T1 s, the same curve on every key, so nothing jitters.
Args: <in glb> <out glb> <clip:side:t0:t1:amp deg> ..."""
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
    parts = job.split(':'); clip, side, t0, t1, amp = parts[:5]; t0, t1, amp = float(t0), float(t1), np.radians(float(amp))
    axis = parts[5] if len(parts) > 5 else 'z'      # Njam: 'x' = about the figure's side-to-side axis (negative swings the arm forward: a hand off the belly)
    n = names.index(f'Bip01 {side} UpperArm'); pa = m.parent[n]
    an = next(a for a in d['animations'] if a['name'] == clip)
    ch = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
    sm = an['samplers'][ch['sampler']]
    T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
    ax = np.array([0, 0, 1.0]) * (1 if side == 'L' else -1) if axis == 'z' else np.array([1.0, 0, 0])      # glTF +z forward: + turns the left arm up and out
    out = []
    for t, q in zip(T, Q):
        u = np.clip((t - t0) / (t1 - t0), 0, 1); a = amp * 0.5 * (1 - np.cos(2 * np.pi * u))
        W = m.world(m.sample(clip, float(t)))
        P = W[pa][:3, :3]; Pn = P / np.linalg.norm(P[0])
        Rn = Pn.T @ rot(ax, a) @ Pn @ qm(q)
        q2 = matrix_quaternion(Rn); out.append(q2 if q2 @ q >= 0 else -q2)
    sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
    print('ARMOUT', job)
g.write(Path(OUT))
