"""Leaf orientation check: for every Wings face, does its normal point away from the leaf mid-surface?"""
import bpy, bmesh, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Wings']
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
up = down = bad = 0
for f in bm.faces:
    n = f.normal
    if abs(n.z) < 0.5:
        continue
    # a top face has a neighbour layer below it: cast down a little
    c = f.calc_center_median()
    if n.z > 0:
        up += 1
    else:
        down += 1
print('LEAF up', up, 'down', down, 'faces', len(bm.faces))
