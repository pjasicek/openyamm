"""Rest-pose visibility of every source face (work/mesh_in.npz order): a face is visible when a ray from just above
its centre escapes the mesh in at least one of 42 directions over its outward hemisphere (as visible_only.py).
-> work/visible.npy. Usage: blender -b -P vis_faces.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); v, f = d['verts'], d['faces']
tree = BVHTree.FromPolygons([Vector(p) for p in v.tolist()], f.tolist())
rng = np.random.default_rng(0); dirs = rng.normal(size=(42, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
vis = np.zeros(len(f), bool)
for i in range(len(f)):
    t = v[f[i]]; n = np.cross(t[1] - t[0], t[2] - t[0]); n /= np.linalg.norm(n) + 1e-12; c = t.mean(0) + n * 1e-4
    for dd in dirs:
        if dd @ n > .1 and tree.ray_cast(Vector(c), Vector(dd), 3.0)[0] is None:
            vis[i] = True; break
np.save(os.path.join(HERE, 'work', 'visible.npy'), vis)
print('VISIBLE', int(vis.sum()), 'of', len(f))
