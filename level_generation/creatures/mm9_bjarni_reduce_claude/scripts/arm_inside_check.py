#!/usr/bin/env python3
"""Second opinion on arm_hand_gate --exact readings (Markel reduction): the gate signs the depth by the normal of the single nearest
triangle, which at a convex vertex shared by several faces (a tie) can read a point 5-6 cm out in the open air as 'inside'.
For one clip frame (48 fps) and side: every forearm/hand vertex the gate's rule reads as inside (> 1 cm), then a parity test with
26 rays against the rest of the body (both primitives, every face not on that arm): inside only if most rays cross an odd number of
faces. Prints the gate-rule count and depth and the parity-confirmed count and depth. Usage: arm_inside_check.py <glb> <clip> <frame48 | all> <tok>  (all: every 48 fps frame, worst per clip)"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, clip, frs, tok = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [0, 1]; tris, dom, off = [], [], 0
for k in USE:
    tris.append(np.asarray(P[k]['triangles']).reshape(-1, 3) + off); off += len(P[k]['positions'])
    dom.append(np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
ARM = 'Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist'.split(',')
LOW = 'Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky'.split(',')
av = np.array([tok in x and any(a in x for a in ARM) for x in dom]); lv = np.flatnonzero([tok in x and any(a in x for a in LOW) for x in dom])
bf = np.flatnonzero(~av[tris].any(1))
def frame(fr):
    X = np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, fr / 48.0)))) if k in USE])
    T = X[tris[bf]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[lv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
    q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, best], n[near[r, best]])
    dep = np.where((side < 0) & (d[r, best] <= 0.06), -side, 0)
    return pts, dep, a, b, c


g = np.array([[x, y, z] for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)], float)
g /= np.linalg.norm(g, axis=1, keepdims=True); g = g @ np.linalg.qr(np.random.default_rng(1).normal(size=(3, 3)))[0]


def inside(p, a, b, c):
    e1, e2 = b - a, c - a
    odd = 0
    for dv in g:
        h = np.cross(dv, e2); det = (e1 * h).sum(1); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = p - a; u = (s * h).sum(1) * inv; qv = np.cross(s, e1); v = (qv * dv).sum(1) * inv; t = (e2 * qv).sum(1) * inv
        odd += int((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)).sum() % 2)
    return odd > len(g) / 2


frames = range(int(round(max(m.clip_times(clip)) * 48)) + 1) if frs == 'all' else [int(frs)]
wg = (0.0, 0, 0); wc = (0.0, 0, 0)
for fr in frames:
    pts, dep, a, b, c = frame(fr)
    flag = np.flatnonzero(dep > 0.01); conf = [i for i in flag if inside(pts[i], a, b, c)]
    if dep.max() > wg[0]:
        wg = (float(dep.max()), fr, len(flag))
    cd = max([dep[i] for i in conf], default=0.0)
    if cd > wc[0]:
        wc = (float(cd), fr, len(conf))
print(f'{clip}{tok}gate rule worst {wg[0]*100:.1f} cm @f{wg[1]} ({wg[2]} verts > 1 cm) | parity-confirmed worst {wc[0]*100:.1f} cm @f{wc[1]} ({wc[2]} verts)')
