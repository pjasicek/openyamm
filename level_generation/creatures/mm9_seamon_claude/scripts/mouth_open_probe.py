"""Openness probe: virtually close the jaw (jaw-weighted verts rotated about PIVOT), then cast hemisphere rays from each
head face; write per-loop-triangle openness (fraction of rays escaping). Args: <blend> <out npy> [angle] [pz] [py]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ang = float(argv[2]) if len(argv) > 2 else 45
pz = float(argv[3]) if len(argv) > 3 else 0.47
py = float(argv[4]) if len(argv) > 4 else -1.57
ob = bpy.data.objects['Body']; me = ob.data
me.calc_loop_triangles()
gi = ob.vertex_groups['Bone08'].index
piv = Vector((0, py, pz))
R = Matrix.Rotation(math.radians(-ang), 3, 'X')
P = []
for v in me.vertices:
    w = sum(g.weight for g in v.groups if g.group == gi)
    q = R @ (v.co - piv) + piv
    P.append(v.co.lerp(q, w))
tris = [t.vertices[:] for t in me.loop_triangles]
bvh = BVHTree.FromPolygons(P, tris)
rng = np.random.default_rng(3)
K = 64
dirs = rng.normal(size=(K, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
out = np.ones(len(tris))
for i, t in enumerate(tris):
    a, b, c = (P[j] for j in t)
    cen = (a + b + c) / 3
    if cen.y > -1.15:
        continue
    n = (b - a).cross(c - a)
    if n.length < 1e-12:
        out[i] = 0.5; continue
    n.normalize()
    free = 0; tot = 0
    for d in dirs:
        d = Vector(d)
        if d.dot(n) < 0:
            d = -d
        tot += 1
        hit = bvh.ray_cast(cen + n * 0.002 + d * 0.001, d, 4.0)
        if hit[0] is None:
            free += 1
    out[i] = free / tot
np.save(argv[1], out)
print('OPEN done', (out < 0.2).sum())
