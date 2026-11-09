"""Which faces of the Monk's head piece (face, neck and the cropped hair inside the hood) can be seen: a ray from just
above the face centre escapes the rest-pose source in at least one of 42 directions over its outward hemisphere.
The back of the head and the hair sit inside the hood and can take a harder cut. -> work/head_visible.npy (bool per
source face; False for faces outside the head piece). Usage: blender -b -P head_visible.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); v, f = d['verts'], d['faces']
lab = np.load(os.path.join(HERE, 'work', 'face_labels.npz'))
tree = BVHTree.FromPolygons([Vector(p) for p in v.tolist()], f.tolist())
rng = np.random.default_rng(0); dirs = rng.normal(size=(42, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
vis = np.zeros(len(f), bool)
for i in np.where(lab['piece'] == 1)[0]:
    t = v[f[i]]; n = np.cross(t[1] - t[0], t[2] - t[0]); n /= np.linalg.norm(n) + 1e-12; c = t.mean(0) + n * 1e-4
    for dd in dirs:
        if dd @ n > .1 and tree.ray_cast(Vector(c), Vector(dd), 3.0)[0] is None:
            vis[i] = True; break
np.save(os.path.join(HERE, 'work', 'head_visible.npy'), vis)
print('HEADVIS', int((lab['piece'] == 1).sum()), 'head faces,', int(vis.sum()), 'visible')
