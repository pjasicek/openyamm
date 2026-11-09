#!/usr/bin/env python3
"""forad-reduce2 probe: at one clip/frame (48 fps) find the deepest hand vertex of one side inside the outer body (the creature's
arm_hand_gate.py --outer-only --exact method) and report the body face it is behind: primitive, face, whether it is an installed face
(same vertex triple as in the installed LOD0) or a new collapse face, and the installed faces around that point.
Usage: probe_hand_depth.py <glb> <clip> <frame48> <L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor')); sys.path.insert(0, str(C / 'claude_shared'))
sys.path.insert(0, str(C / 'mm9_forad_claude' / 'v2' / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from outer_surface import outer_faces  # noqa: E402
glb, clip, fr, side = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
HAND = 'Hand,Finger,Thumb,Index,Middle,Ring,Pinky'.split(','); ARM = 'Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist'.split(',')


def load(path):
    m = Model(Glb(Path(path))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
    tri, dom, off, pid = [], [], 0, []
    for k in USE:
        pr = P[k]; tri.append(pr['triangles'] + off); off += len(pr['positions']); pid += [k] * len(pr['triangles'])
        dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
    return m, USE, np.concatenate(tri), np.concatenate(dom), np.array(pid), jn


def posed(m, USE, clip, t):
    sp = m.skinned_positions(m.world(m.sample(clip, t) if clip else {}))
    return np.concatenate([sp[k][0] for k in USE])


m, USE, tris, dom, pid, jn = load(glb)
tok = f' {side} '
hj = [j for j in jn if tok in j and any(k in j for k in HAND)]; aj = [j for j in jn if tok in j and any(k in j for k in ARM)]
hv = np.where(np.isin(dom, hj))[0]; av = np.isin(dom, aj)
body_f = np.where(~av[tris].any(1))[0]
rest = posed(m, USE, None, 0); body_f = body_f[outer_faces(rest, tris, body_f)]
X = posed(m, USE, clip, fr / 48.0)
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
sd = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
dep = np.where((sd < 0) & (d[rows, best] <= 0.06), -sd, 0.0)
order = np.argsort(-dep)[:5]
src = load(str(C / 'mm9_forad_reduce_claude' / 'before' / 'mm9_forad.glb'))
sp_t = {tuple(sorted(t)) for t in src[2]}
for i in order:
    if dep[i] <= 0: break
    f = body_f[near[i, best[i]]]
    print(f'hand vertex {hv[i]} ({dom[hv[i]]}) depth {dep[i]*100:.2f} cm behind face {f} prim {pid[f]} dom {dom[tris[f]]} '
          f'installed-face {tuple(sorted(tris[f])) in sp_t} at {np.round(pts[i], 3)}')
