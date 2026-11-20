"""Cutter sanity: manifold, self-intersections, and inside tests of given points. Args: -- <blend> x,y,z ..."""
import bpy, sys, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
c = bpy.data.objects['MouthCutter']; me = c.data
bm = bmesh.new(); bm.from_mesh(me)
print('cutter faces', len(bm.faces), 'nonmanifold', sum(1 for e in bm.edges if not e.is_manifold),
      'zero-area', sum(1 for f in bm.faces if f.calc_area() < 1e-9))
bvh = BVHTree.FromBMesh(bm)
print('self-overlap pairs', len(bvh.overlap(bvh)))
for s in a[1:]:
    p = Vector([float(t) for t in s.split(',')]); n = 0; o = p.copy(); d = Vector((0.0123, 0.0071, 1)).normalized()
    while True:
        h = bvh.ray_cast(o, d, 10)
        if h[0] is None: break
        n += 1; o = h[0] + d * 1e-5
    print('point', s, 'hits up', n, 'inside' if n % 2 else 'outside')
# cross-section at y=-4.039 near x 0.3..0.5
for y in (-4.088, -4.039, -3.972):
    hits = []
    for z in np.arange(14.95, 15.15, 0.005):
        h = bvh.ray_cast(Vector((2, y, z)), Vector((-1, 0, 0)), 5)
        if h[0] is not None: hits.append((round(z, 3), round(h[0].x, 3)))
    print('y', y, 'outer x of cutter by z', hits[::4])
