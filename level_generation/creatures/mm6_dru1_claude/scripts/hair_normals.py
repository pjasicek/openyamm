"""Hair shades as one outward surface (review 5: the black jagged band above the forehead was the curled inner side of
the thin hair shell - double-sided material, inward/downward normals, lights from above). Every hair corner (piece 1)
gets a custom split normal: the outward normal of the nearest scalp/skin point (piece 0), so both sides of the shell
shade like the head under it (the usual normal transfer for hair cards). Other corners keep their normals. glTF
exports the custom normals. In place on <blend>. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = [v.co.copy() for v in me.vertices]
skin = [tuple(p.vertices) for p in me.polygons if all(pv[i] == 0 for i in p.vertices)]
tree = BVHTree.FromPolygons(co, skin)
normals = [l.normal.copy() for l in me.loops] if hasattr(me.loops[0], 'normal') else [me.corner_normals[i].vector.copy() for i in range(len(me.loops))]
vn = {}
for v in me.vertices:
    if pv[v.index] == 1:
        loc, n, i, d = tree.find_nearest(v.co, 0.08)
        vn[v.index] = n.normalized() if loc is not None else v.normal.copy()
changed = 0
for p in me.polygons:
    if pv[p.vertices[0]] != 1:
        continue
    for li in p.loop_indices:
        normals[li] = vn[me.loops[li].vertex_index]; changed += 1
me.normals_split_custom_set(normals)
bpy.ops.wm.save_mainfile()
print('HAIRNORMALS corners', changed)
