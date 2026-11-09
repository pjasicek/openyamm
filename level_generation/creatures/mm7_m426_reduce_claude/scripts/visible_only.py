"""Keep only the flagged faces (drift / fleck .npy, value > 40) of a ladder mesh (work/mesh_<tag>.npz) that can be seen:
a face counts as visible when a ray from just above its centre escapes the rest-pose mesh in at least one of 42
directions over its outward hemisphere (MM8 Cleric: many flecks sit on hidden skin under the vest and robe).
Writes work/drift_<out>.npy. Usage: blender -b -P visible_only.py -- <tag> <drift .npy> <out tag>"""
import os, sys, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tag, dpath, out = sys.argv[sys.argv.index('--') + 1:][:3]
d = np.load(os.path.join(HERE, 'work', f'mesh_{tag}.npz')); v, f = d['verts'], d['faces']
drift = np.load(os.path.join(HERE, dpath))
tree = BVHTree.FromPolygons([Vector(p) for p in v.tolist()], f.tolist())
rng = np.random.default_rng(0); dirs = rng.normal(size=(42, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
res = np.zeros(len(f))
for i in np.where(drift > 40)[0]:
    t = v[f[i]]; n = np.cross(t[1] - t[0], t[2] - t[0]); n /= np.linalg.norm(n) + 1e-12; c = t.mean(0) + n * 1e-4
    for dd in dirs:
        if dd @ n <= .1:
            continue
        if tree.ray_cast(Vector(c), Vector(dd), 2.0)[0] is None:
            res[i] = drift[i]; break
np.save(os.path.join(HERE, 'work', f'drift_{out}.npy'), res)
print('VISIBLE', int((drift > 40).sum()), '->', int((res > 40).sum()), [tuple(np.round(v[f[i]].mean(0), 3)) for i in np.where(res > 40)[0]])
