#!/usr/bin/env python3
"""Halberd out of the body (from mm9_imp_claude/scripts/trident_clear.py): per key the deepest shaft point behind the skin (not the fist) is pushed out along the surface normal by a rotation
of Xbase about the fist (rotation and translation, the bone sits at the butt). The angles are a running maximum over +/- HOLD s and a Gaussian of SIGMA s, never per key, as a rotation about one
smoothed axis per contact. The arm and hand keep MM9's motion. Usage: pole_clear.py in.glb out.glb CLIP [CLIP...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
src, dst, *clips = sys.argv[1:]
SIGMA, HOLD, CLEAR, FPS = 0.09, 0.1, 0.015, 30
g = Glb(Path(src)); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
P = [(k, p) for k, p in enumerate(m.primitives) if p['node'] == m.primitives[0]['node'] and p['skinned']]
tri, off, dom = [], 0, []
for k, p in P:
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom)
item = dom == 'Xbase'
hand = np.array([any(k in d for k in (' R Hand', ' R Finger', ' R Thumb', ' R Index', ' R Middle', ' R Ring', ' R Pinky')) for d in dom])
uvs = np.concatenate([np.asarray(g.accessor(pr['attributes']['TEXCOORD_0'])) for pr in g.json['meshes'][0]['primitives'][:len(P)]])
ua = uvs[tri]; uvarea = np.abs((ua[:, 1, 0] - ua[:, 0, 0]) * (ua[:, 2, 1] - ua[:, 0, 1]) - (ua[:, 2, 0] - ua[:, 0, 0]) * (ua[:, 1, 1] - ua[:, 0, 1]))
body_f = np.where(~(item[tri].any(1) | hand[tri].any(1)) & (uvarea > 1e-9))[0]
rest = np.concatenate([p['positions'] for _, p in P])
iv = np.where(item)[0]
ax = np.linalg.svd(rest[iv] - rest[iv].mean(0))[2][0]
tt = rest[iv] @ ax
E0, E1 = iv[tt.argmin()], iv[tt.argmax()]
yb = idx['Xbase']; par = m.parent[yb]; PAR_HAND = par
ani = next(a for a in g.json['animations'])


def rotvec(R):
    """axis-angle vector of a rotation matrix"""
    ang = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if ang < 1e-8:
        return np.zeros(3)
    return np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) * ang / (2 * np.sin(ang))


def rot(v):
    a = np.linalg.norm(v)
    if a < 1e-9:
        return np.eye(3)
    k = v / a
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def m2q(M):
    t = np.trace(M)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        return np.array([(M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s, s / 4])
    i = int(np.argmax(np.diag(M))); j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(M[i, i] - M[j, j] - M[k, k] + 1) * 2
    q = np.zeros(4); q[i] = s / 4; q[3] = (M[k, j] - M[j, k]) / s
    q[j] = (M[j, i] + M[i, j]) / s; q[k] = (M[k, i] + M[i, k]) / s
    return q


def fist(w):
    return (w[PAR_HAND] @ FIST_LOCAL)[:3]


def need(clip, t):
    """rotation vector in the parent's frame that clears the deepest point at time t (zero if clear)"""
    w = m.world(m.sample(clip, float(t)))
    sp = m.skinned_positions(w)
    X = np.concatenate([sp[k][0] for k, _ in P])
    a0, a1 = X[E0], X[E1]
    pts = a0 + np.outer(np.linspace(0, 1, 240), a1 - a0)
    T = X[tri[body_f]]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=16)
    q, _ = closest_on_triangles(np.repeat(pts, 16, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, 16, 0) - q, axis=1).reshape(near.shape)
    best = d.argmin(1); rows = np.arange(len(pts))
    nn = n[near[rows, best]]
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], nn)
    dep = np.where((side < 0) & (d[rows, best] <= 0.06) & (np.abs(side) > 0.9 * d[rows, best]), d[rows, best], 0.0)
    if dep.max() <= 0:
        return np.zeros(3), 0.0
    i = int(dep.argmax())
    C = fist(w)
    r = pts[i] - C
    L = np.linalg.norm(r)
    ang = (dep[i] + CLEAR) / max(L, 0.05)
    axis = np.cross(r / L, nn[i]); axis /= max(np.linalg.norm(axis), 1e-9)
    Rp = w[par][:3, :3]
    Rp = Rp / np.linalg.norm(Rp[:, 0])
    return Rp.T @ (axis * ang), float(dep[i])


w0 = m.world({})
Xa, Xb = rest[E0], rest[E1]
hp = w0[PAR_HAND][:3, 3]; u_ = (Xb - Xa) / np.linalg.norm(Xb - Xa)
gc = Xa + u_ * ((hp - Xa) @ u_)                                  # the shaft point nearest the wrist: the fist, to within a few cm
FIST_LOCAL = np.linalg.inv(w0[PAR_HAND]) @ np.r_[gc, 1]
anim_by_name = {a['name']: a for a in g.json['animations']}
acc = g.json['accessors']
for clip in clips:
    a = anim_by_name[clip]
    ch = next(c for c in a['channels'] if c['target']['node'] == yb and c['target']['path'] == 'rotation')
    ct = next((c for c in a['channels'] if c['target']['node'] == yb and c['target']['path'] == 'translation'), None)
    s = a['samplers'][ch['sampler']]
    times = g.accessor(s['input'])[:, 0]
    Q = g.accessor(s['output']).astype(np.float64)
    if ct is None:
        Tr = np.tile(np.array(g.json['nodes'][yb].get('translation', [0, 0, 0]), float), (len(times), 1))
        a['samplers'].append(dict(input=s['input'], output=0, interpolation='LINEAR'))
        ct = dict(sampler=len(a['samplers']) - 1, target=dict(node=yb, path='translation')); a['channels'].append(ct)
    else:
        st_ = a['samplers'][ct['sampler']]; tt = g.accessor(st_['input'])[:, 0]; Tr = g.accessor(st_['output']).astype(np.float64)
        if len(tt) != len(times):
            Tr = np.c_[[np.interp(times, tt, Tr[:, k]) for k in range(3)]].T
    st = a['samplers'][ct['sampler']]
    V = np.zeros((len(times), 3)); dep = np.zeros(len(times))
    for i, t in enumerate(times):
        V[i], dep[i] = need(clip, t)
    mag = np.linalg.norm(V, axis=1)
    if mag.max() <= 0:
        st['input'] = s['input']; st['output'] = g.append_accessor(Tr.astype(np.float32), 'VEC3')
        print('CLEAR', clip, 'nothing'); continue
    h = max(1, int(round(HOLD * FPS)))
    smag = np.minimum(gaussian_filter1d(maximum_filter1d(mag, 2 * h + 1, mode='nearest'), SIGMA * FPS, mode='nearest'), np.radians(8.0))     # a contact near the fist must not swing the whole pole
    win = smag > 1e-3
    lab = np.cumsum(np.r_[0, np.diff(win.astype(int)) == 1])
    newQ = Q.copy(); newT = Tr.copy()
    fl = FIST_LOCAL[:3]
    for w_ in np.unique(lab[win]):
        idw = np.where(win & (lab == w_))[0]
        v = V[idw].sum(0)
        u = v / max(np.linalg.norm(v), 1e-9)
        for i in idw:
            R = rot(u * smag[i])
            newQ[i] = m2q(R @ q2m(Q[i])); newT[i] = fl + R @ (Tr[i] - fl)
    s['output'] = g.append_accessor(newQ.astype(np.float32), 'VEC4')
    st['input'] = s['input']; st['output'] = g.append_accessor(newT.astype(np.float32), 'VEC3')
    print('CLEAR', clip, 'max tilt %.1f deg, depth %.1f cm, keys %d' % (np.degrees(smag.max()), dep.max() * 100, int(win.sum())))
    m = Model(g)
g.write(Path(dst))
