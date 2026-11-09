"""Which hand vertices the exact gate calls deep, and against which body faces. Args: glb clip t side-token"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared'); sys.path.insert(0, 'scripts')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from scipy.spatial import cKDTree
glb, clip, t, tok = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
g = Glb(Path(glb)); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tri, off, dom = [], 0, []
for k in USE:
    pr = P[k]; tri.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom)
sp = m.skinned_positions(m.world(m.sample(clip, t))); X = np.concatenate([sp[k][0] for k in USE])
hv = np.nonzero([tok in d and any(k in d for k in ('Hand', 'Finger', 'Tip', 'Pinky')) for d in dom])[0]
arm = np.array([(tok in d and any(k in d for k in ('Clavicle','UpperArm','Forearm','Hand','Finger','Tip','Pinky'))) or d.startswith('Box') for d in dom])
ok = ~(arm[tri].any(1))
T = X[tri[ok]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
_, near = cKDTree((a + b + c) / 3).query(X[hv], k=40)
pts = X[hv]
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(-1, 40); best = d.argmin(1); r = np.arange(len(pts))
side = np.einsum('ij,ij->i', pts - q.reshape(-1, 40, 3)[r, best], n[near[r, best]])
dep = np.where((side < 0) & (d[r, best] < .06), -side, 0)
o = np.argsort(-dep)[:6]
fi = np.nonzero(ok)[0][near[r, best]]
for i in o:
    print(round(dep[i] * 100, 1), dom[hv[i]], pts[i].round(3), 'face bones', set(dom[tri[fi[i]]].tolist()))
