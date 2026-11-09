"""Which vertices of part A lie outside the closed surface of part B (ray parity along +x and -z)? Args: blend partA partB [ymin]"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; pA, pB = int(a[1]), int(a[2])
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces); pl = bm.verts.layers.int['part']
fB = [f for f in bm.faces if all(v[pl] == pB for v in f.verts)]
tree = BVHTree.FromPolygons([v.co[:] for v in bm.verts], [[v.index for v in f.verts] for f in fB])
def inside(p):
    votes = 0
    for d in (Vector((1, 0, 0)), Vector((0, 0, -1)), Vector((0, 1, 0))):
        c = 0; o_ = p.copy()
        for _ in range(50):
            h = tree.ray_cast(o_, d)
            if h[0] is None: break
            c += 1; o_ = h[0] + d * 1e-5
        votes += c % 2
    return votes >= 2
V = [v for v in bm.verts if v[pl] == pA]
out = np.array([not inside(v.co) for v in V]); P = np.array([v.co[:] for v in V])
print('PROBE', len(V), 'outside', int(out.sum()))
for y0 in np.arange(-1.0, 0.0, 0.05):
    m = (P[:, 1] >= y0) & (P[:, 1] < y0 + 0.05)
    if m.sum(): print(f'y {y0:5.2f} n {m.sum():4d} outside {int(out[m].sum()):4d} z-out {P[m & out, 2].min() if (m & out).any() else 0:.2f}..{P[m & out, 2].max() if (m & out).any() else 0:.2f}')
