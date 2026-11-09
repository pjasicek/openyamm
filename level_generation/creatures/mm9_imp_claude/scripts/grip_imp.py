#!/usr/bin/env python3
"""Solve the imp's right fist round the trident shaft, for OUR fingers (MM9's constant curl was made for its thin
fingers and a mitten-like palm). Runs on the rigged export (bind pose): glTF coordinates.

Shaft direction: MM9's (the prongs must point where MM9's point in every clip). Position: moved from MM9's Yweaponbase
to the palm side of our knuckles. Each digit curls about one axis (perpendicular to its proximal phalanx, nearest the
shaft axis) with three angles by grid search, so that sample points on the phalanges sit at shaft radius + the digit's
half-thickness from the axis, never inside. Writes work/grip.json: node-local constant rotations for the R finger joints
and the new Yweaponbase position (bind, glTF). Usage: grip_imp.py <rig glb> <out json>"""
import json, sys, itertools
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
sys.path.insert(0, 'scripts')
from glb_pose import Glb

R_SHAFT = 0.0095
G = Glb(sys.argv[1])
doc = G.json
names = [n.get('name', '') for n in doc['nodes']]
idx = {n: i for i, n in enumerate(names)}
par = {}
for i, n in enumerate(doc['nodes']):
    for c in n.get('children', []):
        par[c] = i


def q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def m2q(M):
    t = np.trace(M)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        q = [(M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(M))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(M[i, i] - M[j, j] - M[k, k] + 1) * 2
        q = [0, 0, 0, 0]
        q[i] = s / 4; q[3] = (M[k, j] - M[j, k]) / s
        q[j] = (M[j, i] + M[i, j]) / s; q[k] = (M[k, i] + M[i, k]) / s
    return [float(x) for x in q]


def world(i):
    M = np.eye(4)
    chain = []
    while i is not None:
        chain.append(i); i = par.get(i)
    for k in reversed(chain):
        n = doc['nodes'][k]
        L = np.eye(4); L[:3, :3] = q2m(n.get('rotation', [0, 0, 0, 1])) @ np.diag(n.get('scale', [1, 1, 1])); L[:3, 3] = n.get('translation', [0, 0, 0])
        M = M @ L
    return M


W = lambda n: world(idx[n])
HAND = 'Bip01 R Hand'
Wh = W(HAND)
d = np.array([0.0093, -0.0524, 1.0]); d /= np.linalg.norm(d)        # MM9 shaft axis, butt -> prongs, bind
CH = {k: [f'Bip01 R Finger{k}', f'Bip01 R Finger{k}1', f'Bip01 R Finger{k}2'] for k in range(4)}
# skin, mesh of the fingers: tips from the vertices farthest along each chain
prim = doc['meshes'][0]['primitives'][0]
POS = np.vstack([G.accessor(p['attributes']['POSITION']) for p in doc['meshes'][0]['primitives']])
skin = doc['skins'][0]
jn = [names[j] for j in skin['joints']]
Vs = []
Js = []
for p in doc['meshes'][0]['primitives']:
    Vs.append(G.accessor(p['attributes']['POSITION'])); Js.append((G.accessor(p['attributes']['JOINTS_0']), G.accessor(p['attributes']['WEIGHTS_0'])))
# mesh node transform is identity for skinned exports; world bind = world of the mesh (armature lifted): use IBM consistency
Mesh2W = None
IBM = G.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
k0 = jn.index(HAND)
Mesh2W = Wh @ IBM[k0]
P = np.vstack(Vs); J_ = np.vstack([a for a, _ in Js]); W_ = np.vstack([b for _, b in Js])
P = (Mesh2W[:3, :3] @ P.T).T + Mesh2W[:3, 3]
tips = {}
for k, ch in CH.items():
    ids = [jn.index(c) for c in ch]
    m = np.isin(J_.astype(int), ids[-1:]).any(1) & (W_.max(1) > 0.4)
    vs = P[m]
    p0 = W(ch[-1])[:3, 3]
    tips[k] = vs[np.argmax(np.linalg.norm(vs - p0, axis=1))]
chain = {k: np.array([W(c)[:3, 3] for c in ch] + [tips[k]]) for k, ch in CH.items()}
kn = np.array([chain[k][0] for k in (1, 2, 3)])
f = np.mean([chain[k][1] - chain[k][0] for k in (1, 2, 3)], 0); f /= np.linalg.norm(f)
print('finger dir', f.round(3), 'shaft', d.round(3), 'angle', round(float(np.degrees(np.arccos(abs(f @ d)))), 1))
# palm side: the side MM9's curl closes to
ax = np.linalg.svd(kn - kn.mean(0))[2][0]
n1 = np.cross(f, ax); n1 /= np.linalg.norm(n1)
wrist = Wh[:3, 3]
thumb_side = (chain[0][-1] - kn.mean(0)) @ n1
n = n1 if thumb_side > 0 else -n1
print('palm normal', n.round(3), 'knuckle spread', ax.round(3))
half = [0.0115, 0.0095, 0.0075, 0.005]


def solve(k, C, d=d):
    """three curl angles of digit k round the axis line through C with direction d"""
    pts = chain[k]
    prox = pts[1] - pts[0]; prox /= np.linalg.norm(prox)
    a = d - (d @ prox) * prox; a /= np.linalg.norm(a)
    # sign: curling moves the phalanx toward the shaft
    if np.cross(a, prox) @ (C - pts[0]) < 0:
        a = -a

    def rot(t):
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
        return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K

    segs = [pts[i + 1] - pts[i] for i in range(3)]
    best = (1e9, None)
    th = np.radians(np.arange(-30, 111, 6))
    for t0, t1, t2 in itertools.product(th, np.radians(np.arange(0, 111, 6)), np.radians(np.arange(0, 91, 6))):
        Rs = [rot(t0), rot(t0 + t1), rot(t0 + t1 + t2)]
        p = pts[0].copy(); c = 0.0
        for i in range(3):
            q = p + Rs[i] @ segs[i]
            for s in (0.25, 0.5, 0.75, 1.0):
                x = p + (q - p) * s
                v = x - C
                r = np.linalg.norm(v - (v @ d) * d)
                h = half[i] + (half[i + 1] - half[i]) * s
                gap = r - (R_SHAFT + h)
                c += gap * gap * (60 if gap < 0 else 1)
            p = q
        if c < best[0]:
            best = (c, (float(t0), float(t1), float(t2)))
    return best, a, rot


def quality(C):
    tot = 0
    for k in (1, 2, 3):
        tot += solve(k, C)[0][0]
    return tot


km = kn.mean(0)
cands = []
for du in (0.0, 0.01, 0.02, 0.03):
    for dv in (0.015, 0.022, 0.03):
        C = km + f * du + n * dv
        cands.append((quality(C), du, dv))
cands.sort()
print('best placement', cands[:3])
_, du, dv = cands[0]
C = km + f * du + n * dv
out = {}
rep = {}
Rh = Wh[:3, :3]
for k, ch in CH.items():
    (c, ang), a, rot = solve(k, C)
    rep[k] = {'cost': round(c, 6), 'deg': [round(float(np.degrees(x)), 1) for x in ang]}
    Rs = [rot(ang[0]), rot(ang[0] + ang[1]), rot(ang[0] + ang[1] + ang[2])]
    parent_w = Rh
    for i, j in enumerate(ch):
        Rw0 = W(j)[:3, :3]
        Rw = Rs[i] @ Rw0
        out[j] = m2q(parent_w.T @ Rw)
        parent_w = Rw
json.dump({'fixed_local': out, 'shaft_point': C.tolist(), 'shaft_dir': d.tolist(), 'report': rep, 'r_shaft': R_SHAFT}, open(sys.argv[2], 'w'), indent=1)
print(rep, C.round(3))
