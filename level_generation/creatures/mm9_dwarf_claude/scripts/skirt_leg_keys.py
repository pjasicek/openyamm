#!/usr/bin/env python3
"""Keys of the skirt's leg bones SkirtLeg{F,B}_{L,R} (run 2, reweight.py): children of Bip01 Spine, pivots on the cloth at the belt, front and back.
Per key, the thigh's direction (hip to knee) in the Spine's frame gives its swing from rest: sagittal (forward +) and outward. The front bone takes
FOL x the forward swing only, the back bone FOL x the backward swing only, both take FOL_OUT x the outward swing (none inward). No twist: the cloth does
not turn with the thigh's roll. Computed on the clip's own key times (MM9 keys, smooth), so it cannot add jitter. Run after half_keys.py and before
skirt_keys.py, which lifts the hinges for what the thighs still reach. Args: <in glb> <out glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT = sys.argv[1:3]
FOL, FOL_OUT, MAXSAG = float(os.environ.get('FOL', 1.0)), float(os.environ.get('FOL_OUT', 0.8)), np.radians(100)
g = Glb(Path(IN)); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
SP = ix['Bip01 Spine']
w0 = m.world({}); S0 = w0[SP][:3, :3] / np.linalg.norm(w0[SP][:3, :3], axis=0)


def rotv(v):
    a = np.linalg.norm(v)
    if a < 1e-12: return np.eye(3)
    k = v / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def thigh_dir(w, s):
    a = w[ix[f'Bip01 {s} Thigh']][:3, 3]; b = w[ix[f'Bip01 {s} Calf']][:3, 3]
    S = w[SP][:3, :3] / np.linalg.norm(w[SP][:3, :3], axis=0)
    u = S0 @ (S.T @ (b - a))                            # in the rest world axes, the Spine's motion taken out
    return u / np.linalg.norm(u)


def angles(u, s):
    sag = np.arctan2(u[2], -u[1])                        # +z is forward
    out = np.arctan2((1 if s == 'L' else -1) * u[0], -u[1])   # L is +x
    return sag, out


A0 = {s: angles(thigh_dir(w0, s), s) for s in 'LR'}
BONES = [f'SkirtLeg{fb}_{s}' for s in 'LR' for fb in 'FB']
rest_local = {b: (np.array(doc['nodes'][ix[b]].get('translation', [0, 0, 0]), float), np.array(doc['nodes'][ix[b]].get('rotation', [0, 0, 0, 1]), float)) for b in BONES}


def qm(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


# clearance (skirt_gate.py's test): the hinges hold only (1 - leg share) of the hem, so the leg bones carry it; per key the least factor
# F_ in FACTORS on the follow angle that keeps this side's thigh under the outer cloth, smoothed as skirt_keys.py smooths its hinges
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from detached_parts_audit import closest_on_triangles
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
jn = [names[j] for j in m.joints]
J_, W_ = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
sw = (np.isin(J_, sk) * W_).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in PR]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs)])
face = np.where((sw[tri] > 0.01).all(1))[0]
rest = allpos(w0); ft = rest[tri[face]]; n0 = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); c0 = ft.mean(1)
nn = n0 / np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
face = face[((nn * (c0 * [1, 0, 1])).sum(1) > 0) & (np.abs(nn[:, 1]) < 0.6)]
lgw = (np.isin(J_, [i for i, n in enumerate(jn) if n.startswith('SkirtLeg')]) * W_).sum(1)
LEGF = lgw[tri[face]].mean(1) > 0.3                      # cloth the leg bones carry: the hinges clear the rest (skirt_keys.py)
LEGV = {s: np.where((np.isin(J_, [jn.index(f'Bip01 {s} Thigh')]) * W_).sum(1) > 0.5)[0] for s in 'LR'}
FACTORS = [float(x) for x in os.environ.get('FACTORS', '1.0,1.1,1.2,1.3,1.4,1.5').split(',')]
TOL, HOLD, SIGMA = 0.003, 0.06, 0.03
LOOPS = ('Standing', 'Walking', 'Running')


def through(x, s):
    ft = x[tri[face]]; c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    q = x[LEGV[s]]; _, near = cKDTree(c_).query(q, k=24)
    pts = np.repeat(q, near.shape[1], 0)
    qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
    dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
    v = q - qq.reshape(*near.shape, 3)[r, b]; s_ = np.einsum('ij,ij->i', v, n_[near[r, b]]); dist = dd[r, b]
    th = (s_ > 0.002) & (s_ > 0.98 * dist) & (dist < 0.2) & LEGF[near[r, b]]
    return float(s_[th].max()) if th.any() else 0.0


def leg_quats(w, s, f):
    sag, out = angles(thigh_dir(w, s), s)
    dsag = sag - A0[s][0]; dout = max(out - A0[s][1], 0.0); res = {}; pk = 0.0
    for fb in 'FB':
        a = f * FOL * (max(dsag, 0.0) if fb == 'F' else min(dsag, 0.0)); a = float(np.clip(a, -MAXSAG, MAXSAG))
        R = rotv(np.array([0.0, 0.0, (1 if s == 'L' else -1) * min(f * FOL_OUT * dout, MAXSAG)])) @ rotv(np.array([-a, 0.0, 0.0]))
        b = f'SkirtLeg{fb}_{s}'
        res[b] = matrix_quaternion(np.linalg.inv(S0) @ R @ S0 @ qm(rest_local[b][1])); pk = max(pk, abs(a), f * FOL_OUT * dout)
    return res, pk


rep = {}
for an in doc['animations']:
    clip = an['name']
    T = np.array(sorted(m.clip_times(clip)), float); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1)
    Fk = {s: np.ones(n) for s in 'LR'}
    for k, t in enumerate(T):
        loc = m.sample(clip, float(t)); w = m.world(loc)
        for s in 'LR':
            for f in FACTORS:
                qs, _ = leg_quats(w, s, f); l2 = dict(loc)
                for b, q in qs.items(): l2[ix[b]] = [rest_local[b][0].copy(), q, np.ones(3)]
                if through(allpos(m.world(l2)), s) < TOL: break
            Fk[s][k] = f
    mode = 'wrap' if clip in LOOPS else 'nearest'; sz = max(1, int(round(2 * HOLD / max(dt, 1e-6))) | 1)
    for s in 'LR':
        if n > 2: Fk[s] = np.maximum(gaussian_filter1d(maximum_filter1d(Fk[s], sz, mode=mode), SIGMA / max(dt, 1e-6), mode=mode), 1.0)
    Q = {b: [] for b in BONES}; peak = {b: 0.0 for b in BONES}
    for k, t in enumerate(T):
        w = m.world(m.sample(clip, float(t)))
        for s in 'LR':
            qs, pk = leg_quats(w, s, Fk[s][k])
            for b, q in qs.items():
                if Q[b] and np.dot(q, Q[b][-1]) < 0: q = -q
                Q[b].append(q); peak[b] = max(peak[b], pk)
    an['channels'] = [c for c in an['channels'] if names[c['target']['node']] not in BONES]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    doc['accessors'][tacc]['min'] = [float(T.min())]; doc['accessors'][tacc]['max'] = [float(T.max())]
    for b in BONES:
        qa = g.append_accessor(np.array(Q[b], np.float32), 'VEC4')
        an['samplers'].append(dict(input=tacc, output=qa, interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=ix[b], path='rotation')))
    rep[clip] = {b: round(float(np.degrees(v)), 1) for b, v in peak.items()}; rep[clip]['factor'] = {s: round(float(Fk[s].max()), 2) for s in 'LR'}
    print(clip, rep[clip], flush=True)
g.write(Path(OUT))
print('SKIRTLEG keyed', OUT)
