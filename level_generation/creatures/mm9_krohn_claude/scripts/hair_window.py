#!/usr/bin/env python3
"""One hair strand out of the sword over a contact window (orchestrator 2026-11-04: in Death the side strand XhairA01 crossed
the scabbard on the back 3.1 cm for 5 frames as he falls). As spear_window.py, but the strand moves, not the weapon: one turn
R(axis, a * w(t)) of the strand's pivot (e.g. Xhairpiv01) about its own joint, axis fixed in its parent's (the Head's) frame,
w a smoothstep up over EASE s before the first contact, 1 through the contacts, down over EASE s after. The search moves the
strand's skin rigidly by its share of the strand's bones (a close approximation); the written keys are exact.
Usage: hair_window.py in.glb out.glb CLIP PIVOT   (env EASE 0.25)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
from detached_parts_audit import closest_on_triangles

src, dst, clip, pivot = sys.argv[1:5]
EASE = float(os.environ.get('EASE', 0.25))
g = Glb(Path(src)); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; idx = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
P = [(k, p) for k, p in enumerate(m.primitives) if p['node'] == m.primitives[0]['node'] and p['skinned']]
mats = [g.json['materials'][pr['material']]['name'] for pr in g.json['meshes'][0]['primitives'][:len(P)]]
pv_i = idx[pivot]
sub = {pv_i}
for i in m.order:
    if m.parent[i] in sub:
        sub.add(i)
subj = [k for k, j in enumerate(m.joints) if j in sub]
tri, off, dom, isprop, share = [], 0, [], [], []
for (k, p), mt in zip(P, mats):
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
    isprop.append(np.full(len(p['positions']), 'Props' in mt))
    share.append(np.array([sum(w for j, w in zip(p['joints'][v], p['weights'][v]) if j in subj) for v in range(len(p['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom); isprop = np.concatenate(isprop); share = np.concatenate(share)
sword = isprop & (dom != 'Xspear')
strand_f = np.where((share[tri] > 0.5).all(1))[0]
sv = np.where(sword)[0]
ss = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))


def rot(v, a):
    v = v / np.linalg.norm(v); K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def depth(pts, X):
    T = X[tri[strand_f]]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=min(16, len(T)))
    q, _ = closest_on_triangles(np.repeat(pts, near.shape[1], 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, near.shape[1], 0) - q, axis=1).reshape(near.shape)
    best = d.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    return np.where((side < 0) & (d[rows, best] <= 0.15) & (np.abs(side) > 0.9 * d[rows, best]), d[rows, best], 0.0)


dur = max(m.clip_times(clip))
frames = np.arange(0, dur + 1e-6, 1 / 48)
cache = []
for t in frames:
    w = m.world(m.sample(clip, float(t)))
    sp = m.skinned_positions(w)
    X = np.concatenate([sp[k][0] for k, _ in P])
    cache.append((t, w, X))
base = np.array([depth(X[sv], X).max() for _, _, X in cache])
hit = np.where(base > 0.01)[0]
if not len(hit):
    print('HAIRWIN', clip, 'clear'); g.write(Path(dst)); sys.exit()
t0, t1 = frames[hit[0]], frames[hit[-1]]
wt = lambda t: (ss((t - (t0 - EASE)) / EASE) if t < t0 else 1.0) * (ss(((t1 + EASE) - t) / EASE) if t > t1 else 1.0)
use = [c for c in cache if t0 - EASE <= c[0] <= t1 + EASE]
dirs = [np.array(d, float) / np.linalg.norm(d) for d in
        [(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)]]
par = m.parent[pv_i]
best = None
for d_ in dirs:
    for ang in np.radians(np.arange(4, 37, 4)):
        worst = 0.0
        for t, w, X in use:
            Rp = w[par][:3, :3] / np.linalg.norm(w[par][:3, 0]); pv = w[pv_i][:3, 3]
            Rw = Rp @ rot(d_, ang * wt(t)) @ Rp.T
            Y = X.copy()
            Y += share[:, None] * (((X - pv) @ Rw.T + pv) - X)
            worst = max(worst, depth(X[sv], Y).max())
        key = (worst if worst > 0.003 else 0.0, ang)
        if best is None or key < (best[0], best[2]):
            best = (key[0], d_, ang, worst)
_, d_, ang, worst = best
print('HAIRWIN', clip, pivot, 'window %.2f-%.2f s, before %.1f cm, axis %s angle %.0f deg, after %.1f cm (search)' % (
    t0, t1, base.max() * 100, np.round(d_, 2).tolist(), np.degrees(ang), worst * 100))
a = next(a for a in g.json['animations'] if a['name'] == clip)
ch = next(c for c in a['channels'] if c['target']['node'] == pv_i and c['target']['path'] == 'rotation')
s_ = a['samplers'][ch['sampler']]
tr = g.accessor(s_['input'])[:, 0]; Q = g.accessor(s_['output']).astype(float)
out = []
for t, q in zip(tr, Q):
    qn = matrix_quaternion(rot(d_, ang * wt(t)) @ quaternion_matrix(q))
    out.append(qn if qn @ q >= 0 else -qn)
s_['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
g.write(Path(dst))
