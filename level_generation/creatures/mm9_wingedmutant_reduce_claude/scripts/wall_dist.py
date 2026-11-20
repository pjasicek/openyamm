"""Opposite-wall distance per face of work/mesh_in.npz (rest pose): a ray from the centroid along the inward normal
against the mesh without the wing back copies (sets.npz back). Tubes (wing spars, claws, hair locks) have a wall a few
cm away, single membrane sheets none (inf). Writes work/wall.npy. Usage: blender -b -P wall_dist.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); V, F = d['verts'], d['faces']
back = np.load(os.path.join(HERE, 'work', 'sets.npz'))['back']
front = np.flatnonzero(~back)
tree = BVHTree.FromPolygons([tuple(x) for x in V.tolist()], [tuple(x) for x in F[front].tolist()])
dist = np.full(len(F), np.inf)
for i, (a, b, c) in enumerate(F):
    pa, pb, pc = Vector(V[a]), Vector(V[b]), Vector(V[c]); n = (pb - pa).cross(pc - pa)
    if n.length < 1e-12:
        continue
    n.normalize(); o = (pa + pb + pc) / 3 - n * 1e-5
    hit = tree.ray_cast(o, -n, 0.2)
    if hit[0] is not None:
        dist[i] = hit[3]
np.save(os.path.join(HERE, 'work', 'wall.npy'), dist)
print('WALL done', np.isfinite(dist).sum(), 'of', len(F))
