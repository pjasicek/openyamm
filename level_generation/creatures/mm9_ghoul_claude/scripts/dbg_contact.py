import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared'); sys.path.insert(0, 'scripts')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
m = Model(Glb(sys.argv[1])); doc = m.glb.json
names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
rest = np.concatenate([m.skinned_positions(m.world({}))[k][0] for k in USE])
for clip, t, s in ((sys.argv[2], float(sys.argv[3]), sys.argv[4]),):
    tok = f' {s} '
    arm = np.array([tok in d and any(k in d for k in ARM) for d in dom])
    hand = np.array([tok in d and any(k in d for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for d in dom])
    body = np.where(~arm[tris].any(1))[0]; body = body[outer_faces(rest, tris, body)]
    X = np.concatenate([r[0] for r in m.skinned_positions(m.world(m.sample(clip, t)))])
    T = X[tris[body]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    hv = np.where(hand)[0]; pts = X[hv]
    _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
    rp = np.repeat(pts, near.shape[1], 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
    cp = q.reshape(*near.shape, 3)[r, best]; fi = near[r, best]
    side = np.einsum('ij,ij->i', pts - cp, n[fi]); dep = np.where((side < 0) & (d[r, best] <= 0.06), -side, 0)
    o = np.argsort(-dep)[:6]
    for i in o:
        print(round(float(dep[i]) * 100, 1), dom[hv[i]], '->', dom[tris[body[fi[i]]][0]], 'dist', round(float(d[i, best[i]]), 3))
