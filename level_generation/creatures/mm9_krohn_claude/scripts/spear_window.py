#!/usr/bin/env python3
"""The glaive out of the body over one contact window, as ONE smooth turn about the fist (orchestrator 2026-11-04: the shaft
crossed the right shoulder and side hair in AttackMelee's wind-up; spear_clear.py's per-key deepest-point pushes chased
shoulder and hair in turn and stalled at 6 cm).

For CLIP: the contact frames (glaive points behind the skin, as prop_gate.py, 24 fps) give a window [t0 - EASE, t1 + EASE];
a turn R(axis, a * w(t)) about the fist (w: smoothstep up over EASE s before the first contact, 1 through the contacts,
down over EASE s after), axis fixed in the hand's frame, is applied to Xspear's keys (rotation and translation about the
fist, as spear_clear.py). Searched: 26 axes x angles 6..40 deg; picked the smallest angle whose worst depth over the
window is under 1 cm (else the smallest worst depth). The arm and hand keep MM9's motion.
Usage: spear_window.py in.glb out.glb CLIP [CLIP ...]   (env EASE 0.2)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles

src, dst, *clips = sys.argv[1:]
EASE = float(os.environ.get('EASE', 0.2))
g = Glb(Path(src)); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; idx = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
P = [(k, p) for k, p in enumerate(m.primitives) if p['node'] == m.primitives[0]['node'] and p['skinned']]
mats = [g.json['materials'][pr['material']]['name'] for pr in g.json['meshes'][0]['primitives'][:len(P)]]
tri, off, dom, isprop = [], 0, [], []
for (k, p), mt in zip(P, mats):
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
    isprop.append(np.full(len(p['positions']), 'Props' in mt))
tri = np.concatenate(tri); dom = np.concatenate(dom); isprop = np.concatenate(isprop)
spear = isprop & (dom == 'Xspear')
hand = np.array([any(k in d for k in (' R Hand', ' R Index', ' R Middle', ' R Ring', ' R Pinky', ' R Thumb')) for d in dom])
rest = np.concatenate([p['positions'] for _, p in P])
uvs = np.concatenate([np.asarray(g.accessor(pr['attributes']['TEXCOORD_0'])) for pr in g.json['meshes'][0]['primitives'][:len(P)]])
ua = uvs[tri]; uvarea = np.abs((ua[:, 1, 0] - ua[:, 0, 0]) * (ua[:, 2, 1] - ua[:, 0, 1]) - (ua[:, 2, 0] - ua[:, 0, 0]) * (ua[:, 1, 1] - ua[:, 0, 1]))
body_f = np.where(~(isprop[tri].any(1) | hand[tri].any(1)) & (uvarea > 1e-9))[0]
iv = np.where(spear)[0]
ax0 = np.linalg.svd(rest[iv] - rest[iv].mean(0))[2][0]
tt = rest[iv] @ ax0
E0, E1 = iv[tt.argmin()], iv[tt.argmax()]
xs = idx['Xspear']; hd = idx['Bip01 R Hand']
w0 = m.world({})
fistw = np.mean([w0[idx[f'Bip01 R {f}{k}']][:3, 3] for f in ('Index', 'Middle', 'Ring') for k in (1, 2)], 0)
u_ = (rest[E1] - rest[E0]) / np.linalg.norm(rest[E1] - rest[E0])
gc = rest[E0] + u_ * ((fistw - rest[E0]) @ u_)
FIST_H = (np.linalg.inv(w0[hd]) @ np.r_[gc, 1])[:3]          # the fist on the shaft, in the hand's frame


def rot(v, a):
    v = v / np.linalg.norm(v); K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def depth(pts, X):
    T = X[tri[body_f]]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=16)
    q, _ = closest_on_triangles(np.repeat(pts, 16, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, 16, 0) - q, axis=1).reshape(near.shape)
    best = d.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    return np.where((side < 0) & (d[rows, best] <= 0.15) & (np.abs(side) > 0.9 * d[rows, best]), d[rows, best], 0.0)


SAMP = np.linspace(0, 1, 160)
spv = iv
ss = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
dirs = []
for x in (-1, 0, 1):
    for y in (-1, 0, 1):
        for z in (-1, 0, 1):
            if (x, y, z) != (0, 0, 0):
                dirs.append(np.array([x, y, z], float) / np.linalg.norm([x, y, z]))
anim = {a['name']: a for a in g.json['animations']}
for clip in clips:
    dur = max(m.clip_times(clip))
    frames = np.arange(0, dur + 1e-6, 1 / float(os.environ.get('SW_FPS', 48)))
    cache = []
    for t in frames:
        w = m.world(m.sample(clip, float(t)))
        sp = m.skinned_positions(w)
        X = np.concatenate([s[0] for _, s in [(k, sp[k]) for k, _ in P]])
        pts = np.vstack([X[E0] + np.outer(SAMP, X[E1] - X[E0]), X[spv]])
        cache.append((t, w, X, pts))
    base = np.array([depth(c[3], c[2]).max() for c in cache])
    hit = np.where(base > 0.01)[0]
    if not len(hit):
        print('SPEARWIN', clip, 'clear'); continue
    t0, t1 = frames[hit[0]], frames[hit[-1]]
    wt = lambda t: max(ss((t - (t0 - EASE)) / EASE) if t < t0 else 1.0, 0.0) * (ss(((t1 + EASE) - t) / EASE) if t > t1 else 1.0)
    use = [c for c in cache if t0 - EASE <= c[0] <= t1 + EASE]
    best = None
    for d_ in dirs:
        for ang in np.radians(np.arange(6, 41, 4)):
            worst = 0.0
            for t, w, X, pts in use:
                Rh = w[hd][:3, :3] / np.linalg.norm(w[hd][:3, 0])
                pv = w[hd][:3, :3] @ FIST_H + w[hd][:3, 3]
                Rw = Rh @ rot(d_, ang * wt(t)) @ Rh.T
                worst = max(worst, depth((pts - pv) @ Rw.T + pv, X).max())
            key = (worst if worst > 0.003 else 0.0, ang)   # margin: the gate samples more points than this search
            if best is None or key < (best[0], best[2]):
                best = (key[0], d_, ang, worst)
    _, d_, ang, worst = best
    print('SPEARWIN', clip, 'window %.2f-%.2f s, before %.1f cm, axis %s angle %.0f deg, after %.1f cm' % (
        t0, t1, base.max() * 100, np.round(d_, 2).tolist(), np.degrees(ang), worst * 100))
    a = anim[clip]
    chr_ = next(c for c in a['channels'] if c['target']['node'] == xs and c['target']['path'] == 'rotation')
    cht = next(c for c in a['channels'] if c['target']['node'] == xs and c['target']['path'] == 'translation')
    sr, st = a['samplers'][chr_['sampler']], a['samplers'][cht['sampler']]
    tr = g.accessor(sr['input'])[:, 0]; Q = g.accessor(sr['output']).astype(float)
    ttr = g.accessor(st['input'])[:, 0]; Tr = g.accessor(st['output']).astype(float)
    from glb_pose import quaternion_matrix, matrix_quaternion
    newQ = []
    for t, q in zip(tr, Q):
        R = rot(d_, ang * wt(t)); qn = matrix_quaternion(R @ quaternion_matrix(q)[:3, :3] if quaternion_matrix(q).shape[0] == 4 else R @ quaternion_matrix(q))
        newQ.append(qn if qn @ q >= 0 else -qn)
    newT = [FIST_H + rot(d_, ang * wt(t)) @ (T_ - FIST_H) for t, T_ in zip(ttr, Tr)]
    sr['output'] = g.append_accessor(np.array(newQ, np.float32), 'VEC4')
    st['output'] = g.append_accessor(np.array(newT, np.float32), 'VEC3')
    m = Model(g)
g.write(Path(dst))
