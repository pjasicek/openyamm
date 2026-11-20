"""Projection from the rebuilt mallet onto the installed one (Blender, for its BVH): for every texel of
work/mallet_texels.npz a ray from OUT metres outside the new surface along -normal, up to 2*OUT; the first hit on an old
triangle that faces the same way (dot > 0) is the texel's source (the outermost old surface: studs, bands and rings
included). No such hit: the nearest old surface point. Writes work/mallet_hits.npz (old triangle, hit position, kind:
1 ray, 2 nearest). Usage: blender -b --factory-startup -P mallet_rays.py"""
import os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = float(os.environ.get('RAY_OUT', '0.03'))
o = np.load(os.path.join(HERE, 'work', 'mallet_old.npz')); P, I = o['P'].astype(float), o['I']
fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
tree = BVHTree.FromPolygons([tuple(p) for p in P.tolist()], [tuple(t) for t in I.tolist()], all_triangles=True)
t = np.load(os.path.join(HERE, 'work', 'mallet_texels.npz')); pos, nor = t['pos'], t['nor']
face = np.full(len(pos), -1); hit = np.zeros((len(pos), 3)); kind = np.zeros(len(pos), np.int8)
for i in range(len(pos)):
    n = Vector(nor[i]); start = Vector(pos[i]) + n * OUT; d = -n; left = 2 * OUT
    while left > 0:
        loc, _, idx, dd = tree.ray_cast(start, d, left)
        if loc is None:
            break
        if fn[idx] @ nor[i] > 0.0:
            face[i] = idx; hit[i] = loc[:]; kind[i] = 1; break
        start = loc + d * 1e-5; left -= dd + 1e-5
    if face[i] < 0:
        loc, _, idx, _ = tree.find_nearest(Vector(pos[i]))
        face[i] = idx; hit[i] = loc[:]; kind[i] = 2
np.savez(os.path.join(HERE, 'work', 'mallet_hits.npz'), face=face, hit=hit, kind=kind)
print('RAYS', len(pos), 'ray hits', int((kind == 1).sum()), 'nearest fallback', int((kind == 2).sum()))
