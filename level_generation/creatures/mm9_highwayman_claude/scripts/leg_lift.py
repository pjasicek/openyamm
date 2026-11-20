#!/usr/bin/env python3
"""Feet on the floor in walks without a pelvis pop: our leg is a little longer than MM9's, so where MM9's clip has the leg straight the foot goes 14 cm under the floor and the floor pass threw the pelvis up 10 cm at one point of the cycle. Per key and foot the sink lifts the ankle by
two-bone IK (hip and knee bend a little, the foot keeps its world rotation). The lift curve is a running maximum and a circular Gaussian on the clip's keys. Args: <in glb> <out glb> <clip> ..."""
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT, *CLIPS = sys.argv[1:]
g = Glb(Path(IN)); d = g.json; m = Model(g)
names = [n.get('name') for n in d['nodes']]; jn = [names[j] for j in m.joints]; ix = {n: i for i, n in enumerate(names)}
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
unit = lambda v: v / max(np.linalg.norm(v), 1e-9)
def between(a, b):
    a = unit(a); b = unit(b); v = np.cross(a, b); c = float(a @ b); s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
GROUND = 0.0
for clip in CLIPS:
    an = next(a for a in d['animations'] if a['name'] == clip)
    def chan(n):
        ch = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
        return an['samplers'][ch['sampler']]
    T = np.asarray(g.accessor(chan(ix['Bip01 L Thigh'])['input'])).ravel(); dt = (T[-1] - T[0]) / (len(T) - 1)
    S_ = {}
    Ws = [m.world(m.sample(clip, float(t))) for t in T]
    Xs = [allpos(w) for w in Ws]
    for S in 'LR':
        ids = np.where(np.isin(dom, [f'Bip01 {S} Foot', f'Bip01 {S} Toe0', f'Bip01 {S} Foot_h']))[0]
        A = np.array([max(0.0, GROUND - X[ids, 1].min()) for X in Xs])
        S_[S] = gaussian_filter1d(maximum_filter1d(A, 5, mode='wrap'), 0.05 / dt, mode='wrap')
        print('LIFT', clip, S, 'max cm', round(float(A.max()) * 100, 1), 'smoothed', round(float(S_[S].max()) * 100, 1))
    for S in 'LR':
        th, ca, fo = ix[f'Bip01 {S} Thigh'], ix[f'Bip01 {S} Calf'], ix[f'Bip01 {S} Foot']; pa = m.parent[th]
        Qs = {n: [] for n in (th, ca, fo)}
        for k, W in enumerate(Ws):
            H, K_, A_ = W[th][:3, 3], W[ca][:3, 3], W[fo][:3, 3]
            Tg = A_ + np.array([0, S_[S][k], 0])
            L1, L2 = np.linalg.norm(K_ - H), np.linalg.norm(A_ - K_)
            dd = min(np.linalg.norm(Tg - H), L1 + L2 - 1e-4); u = unit(Tg - H)
            a = (L1 ** 2 - L2 ** 2 + dd ** 2) / (2 * dd); h = np.sqrt(max(L1 ** 2 - a ** 2, 0))
            b = (K_ - H) - u * ((K_ - H) @ u)
            if np.linalg.norm(b) < 1e-3: b = np.array([0, 0, 1.0]) - u * u[2]
            K2 = H + u * a + unit(b) * h
            R1 = between(K_ - H, K2 - H)
            A1 = K2 + R1 @ (A_ - K_)
            R2 = between(A1 - K2, Tg - K2)
            def R(i): return W[i][:3, :3] / np.linalg.norm(W[i][:3, 0])
            Wt = R1 @ R(th); Wc = R2 @ R1 @ R(ca); Wf = R(fo)
            Qs[th].append(matrix_quaternion(R(pa).T @ Wt)); Qs[ca].append(matrix_quaternion(Wt.T @ Wc)); Qs[fo].append(matrix_quaternion(Wc.T @ Wf))
        for n, q in Qs.items():
            q = np.array(q)
            for k in range(1, len(q)):
                if q[k] @ q[k - 1] < 0: q[k] *= -1
            chan(n)['output'] = g.append_accessor(q.astype(np.float32), 'VEC4')
g.write(Path(OUT))
