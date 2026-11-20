#!/usr/bin/env python3
"""Toes out of the floor in run cycles: our foot is longer than MM9's, so MM9's toe-off drives it 11 cm under the floor and a per-key floor raise then bobs the pelvis 16 cm. Per key and foot the sink gives the least upward turn of the foot about the ankle;
the curve is a running maximum and a circular Gaussian on the clip's keys, never per frame. Args: <in glb> <out glb> <clip> ..."""
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT, *CLIPS = sys.argv[1:]
g = Glb(Path(IN)); d = g.json; m = Model(g)
names = [n.get('name') for n in d['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
def rot(ax, a):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def qm(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
GROUND = 0.012
for clip in CLIPS:
    an = next(a for a in d['animations'] if a['name'] == clip)
    for S in 'LR':
        n = names.index(f'Bip01 {S} Foot'); pa = m.parent[n]
        ids = np.where(np.isin(dom, [f'Bip01 {S} Foot', f'Bip01 {S} Toe0', f'Bip01 {S} Foot_h']))[0]
        ch = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
        sm = an['samplers'][ch['sampler']]
        T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
        A = np.zeros(len(T)); AX = []
        for k, t in enumerate(T):
            W = m.world(m.sample(clip, float(t))); X = allpos(W)[ids]
            ank = W[n][:3, 3]; low = X[np.argmin(X[:, 1])]; v = low - ank
            sink = max(0.0, GROUND - low[1]); L = max(np.linalg.norm(v), 0.1)
            A[k] = np.arcsin(min(0.9, sink / L)) * 1.15
            AX.append(np.cross(v, [0, 1, 0]))
        dt = (T[-1] - T[0]) / (len(T) - 1)
        S2 = gaussian_filter1d(maximum_filter1d(A, 3, mode='wrap'), 0.03 / dt, mode='wrap')
        out = []
        for k, t in enumerate(T):
            W = m.world(m.sample(clip, float(t))); Pr = W[pa][:3, :3]; Pr = Pr / np.linalg.norm(Pr[0])
            R = Pr.T @ rot(AX[k], S2[k]) @ Pr @ qm(Q[k])
            q2 = matrix_quaternion(R); out.append(q2 if q2 @ Q[k] >= 0 else -q2)
        sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
        print('FOOT', clip, S, 'max deg', round(float(np.degrees(S2.max())), 1))
g.write(Path(OUT))
