"""Per-vertex mirror-to-surface distance of Body in rest pose: distance from (-x, y, z) of each vertex to the mesh
surface. Usage: blender -b <blend> -P mirror_surface.py -- <out.npy>"""
import bpy, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; me = o.data
verts = [o.matrix_world @ v.co for v in me.vertices]
me.calc_loop_triangles(); tris = [t.vertices[:] for t in me.loop_triangles]
bvh = BVHTree.FromPolygons(verts, tris)
d = np.array([bvh.find_nearest(Vector((-v.x, v.y, v.z)))[3] for v in verts])
np.save(out, d); print('MIRROR median/p95/p99/max mm', np.round(np.percentile(d, [50, 95, 99, 100]) * 1000, 2))
