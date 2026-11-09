"""Faces hit by camera rays through pixels of a render_views image (rest pose). Args: -- <blend> <view> <zc> <size>
<res> u,v [u,v ...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
ang = {'front': 0.0, 'three_quarter': 35.0, 'side60': 60.0, 'rside60': -60.0, 'back': 180.0}[a[1]]; zc, size, res = float(a[2]), float(a[3]), int(a[4])
me = bpy.data.objects['Body'].data
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
T = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
r = math.radians(ang); right = Vector((math.cos(r), math.sin(r), 0)); d = Vector((-math.sin(r), math.cos(r), 0))
for uv in a[5:]:
    u, v = (float(x) for x in uv.split(','))
    P = right * ((u / res - 0.5) * size) + Vector((0, 0, zc + (0.5 - v / res) * size)) - d * 3
    h = T.ray_cast(P, d, 6)
    if h[0] is None: print('PICK', uv, 'none'); continue
    p = me.polygons[h[2]]
    print('PICK', uv, 'face', h[2], 'loc', tuple(round(x, 3) for x in h[0]), 'n', tuple(round(x, 2) for x in p.normal), 'piece', pv[p.vertices[0]], 'garment', gv[p.vertices[0]])
