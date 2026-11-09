"""Flatten the hair shell's front lip onto the scalp (review 5: a black jagged band above the forehead was the
underside of the thick hair lip - 56 of 129 front-top hair faces face downward - lit only by the ground term of the
lights). Hair vertices (piece 1) in the front-top region (z > Z0, y < -0.04, |x - axis| < 0.065) move toward the
nearest scalp point: target = scalp point + its normal x (UNDER mm for downward-facing vertices, TOP mm otherwise),
weight 1 inside the region fading over its border; topology, UVs and weights unchanged. In place. Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
Z0, UNDER, TOP, AX = 1.595, 0.0025, 0.006, -0.007
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
if me.get('hair_lip'):
    print('HAIRLIP already flattened'); sys.exit(0)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = [v.co.copy() for v in me.vertices]
skin = [tuple(p.vertices) for p in me.polygons if all(pv[i] == 0 for i in p.vertices)]
tree = BVHTree.FromPolygons(co, skin)
moved = 0; dmax = 0.0
for v in me.vertices:
    if pv[v.index] != 1:
        continue
    p = v.co
    cl = lambda t: min(1.0, max(0.0, t))                  # each factor clamped (two negative factors made w > 0)
    w = cl((p.z - Z0) / 0.012) * cl((-0.04 - p.y) / 0.015) * cl((0.065 - abs(p.x - AX)) / 0.015)
    if w <= 0:
        continue
    loc, n, i, d = tree.find_nearest(p, 0.04)
    if loc is None:
        continue
    off = UNDER if v.normal.z < -0.2 else TOP
    tgt = loc + n * off
    v.co = p.lerp(tgt, w); moved += 1; dmax = max(dmax, (tgt - p).length * w)
me['hair_lip'] = 1; me.update(); bpy.ops.wm.save_mainfile()
print('HAIRLIP vertices', moved, 'max move mm', round(dmax * 1000, 1))
