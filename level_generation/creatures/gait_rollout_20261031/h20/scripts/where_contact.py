import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts')
from gaitlib import glb_pose
from contact_probe import vertex_normals, ARM, TARGET
body = glb_pose.Glb(sys.argv[1]); model = glb_pose.Model(body)
names = [n['name'] for n in body.json['nodes']]
prim = model.primitives[0]
dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
arm = np.array([any(t in d for t in ('Forearm', 'Hand', 'Finger')) for d in dom])
target = np.array([any(t in d for t in TARGET) and not any(t in d for t in ARM) for d in dom])
ai, ti = np.where(arm)[0], np.where(target)[0]
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    for t in np.arange(0, T, T / 16):
        W = model.world(model.sample(clip, float(t)))
        pts = model.skinned_positions(W)[0][0]
        nrm = vertex_normals(pts, prim['triangles'])
        tree = cKDTree(pts[ti]); d, i = tree.query(pts[ai])
        depth = np.einsum('ij,ij->i', pts[ai] - pts[ti][i], nrm[ti][i])
        inside = (d < 0.04) & (depth < -0.002)
        if inside.any():
            k = np.argmin(np.where(inside, depth, 0))
            print(f'{clip} {t/T:.2f} n={inside.sum()} depth {-1000*depth[k]:.0f} mm arm {dom[ai[k]]} target {dom[ti[i[k]]]} at {np.round(pts[ai[k]],3)}')
