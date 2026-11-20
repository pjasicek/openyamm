"""Head skin faces hidden under the hair (scalp): a ray from each skin face's centroid along its outward normal hits a
hair face within COVER m (rest pose). Writes work/skin_covered.npy (per mesh_in face). Usage: blender -b -P skin_cover.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVER = float(os.environ.get('COVER', '0.04'))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); V, F = d['verts'], d['faces']
L = np.load(os.path.join(HERE, 'work', 'glb_labels.npz')); prim, kind = L['prim'], L['kind']
hair = np.flatnonzero((prim == 2) & (kind == 3))
tree = BVHTree.FromPolygons([tuple(x) for x in V.tolist()], [tuple(x) for x in F[hair].tolist()])
skin = np.flatnonzero((prim == 2) & (kind == 1))
cov = np.zeros(len(F), bool); dirs = 0
for i in skin:
    a, b, c = (Vector(V[k]) for k in F[i]); n = (b - a).cross(c - a)
    if n.length < 1e-12:
        continue
    n.normalize(); o = (a + b + c) / 3 + n * 1e-4
    hits = 0
    # the centroid ray and four tilted rays (35 deg): covered only if all hit hair
    t1 = n.orthogonal().normalized(); t2 = n.cross(t1)
    for dv in (n, (n + 0.7 * t1).normalized(), (n - 0.7 * t1).normalized(), (n + 0.7 * t2).normalized(), (n - 0.7 * t2).normalized()):
        if tree.ray_cast(o, dv, COVER)[0] is not None:
            hits += 1
    cov[i] = hits == 5
np.save(os.path.join(HERE, 'work', 'skin_covered.npy'), cov)
print('COVERED', int(cov.sum()), 'of', len(skin), 'skin faces')
