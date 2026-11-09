"""Mirror symmetry of the rest mesh: distance of every vertex (mirrored in x) to the surface, per height band.
Args: <blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data; M = b.matrix_world
co = [M @ v.co for v in me.vertices]
bvh = BVHTree.FromPolygons(co, [list(p.vertices) for p in me.polygons])
d = np.array([bvh.find_nearest(Vector((-v.x, v.y, v.z)))[3] for v in co])
z = np.array([v.z for v in co])
print('SYM all p50 %.1f p95 %.1f max %.1f mm' % (np.median(d) * 1e3, np.percentile(d, 95) * 1e3, d.max() * 1e3))
for lo, hi, n in ((-1, -.5, 'legs'), (-.5, .15, 'skirt'), (.15, .55, 'torso'), (.55, 1, 'head')):
    m = (z > lo) & (z <= hi)
    print('SYM', n, 'p50 %.1f p95 %.1f max %.1f mm' % (np.median(d[m]) * 1e3, np.percentile(d[m], 95) * 1e3, d[m].max() * 1e3))
