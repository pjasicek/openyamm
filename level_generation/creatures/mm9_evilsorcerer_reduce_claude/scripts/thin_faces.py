"""Thin flaps of the closed body skin (loincloth hems, fur flap tips): for every face (sorcerer: every material), a ray from its centroid
along the inward normal; faces whose opposite wall lies within THIN metres are thin sheets (at r74 their tips crossed
and showed the inside as dark teeth along the back hem). Writes work/thin.npy (per dump_mesh face, rest pose).
Usage: blender -b -P thin_faces.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THIN = float(os.environ.get('THIN', '0.012'))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); V, F = d['verts'], d['faces']
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
tree = BVHTree.FromPolygons([tuple(x) for x in V.tolist()], [tuple(x) for x in F.tolist()])
thin = np.zeros(len(F), bool); dist = np.full(len(F), np.inf)
for i, (a, b, c) in enumerate(F):
    pa, pb, pc = Vector(V[a]), Vector(V[b]), Vector(V[c]); n = (pb - pa).cross(pc - pa)
    if n.length < 1e-12:
        continue
    n.normalize(); o = (pa + pb + pc) / 3 - n * 1e-5
    hit = tree.ray_cast(o, -n, 0.1)
    if hit[0] is not None:
        dist[i] = hit[3]
thin = dist < THIN
np.save(os.path.join(HERE, 'work', 'thin.npy'), thin)
c = V[F[thin]].mean(1)
print('THIN', int(thin.sum()), 'faces under', THIN, 'm; z', np.round(np.percentile(c[:, 2], [0, 50, 100]), 3) if thin.any() else '')
