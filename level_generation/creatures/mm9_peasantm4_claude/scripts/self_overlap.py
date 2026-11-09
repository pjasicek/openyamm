"""Count self-intersecting face pairs (non-adjacent) of the Body mesh, by z band. Args: blend [blend ...]"""
import bpy, sys
from mathutils.bvhtree import BVHTree
for path in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body'].data
    vs = [v.co.copy() for v in me.vertices]; ps = [list(p.vertices) for p in me.polygons]
    t = BVHTree.FromPolygons(vs, ps)
    pairs = [(a, b) for a, b in t.overlap(t) if a < b and not set(ps[a]) & set(ps[b])]
    bands = {}
    for a, b in pairs:
        z = round(me.polygons[a].center.z, 1); bands[z] = bands.get(z, 0) + 1
    print('OVERLAP', path.split('/')[-1], len(pairs), sorted(bands.items()))
