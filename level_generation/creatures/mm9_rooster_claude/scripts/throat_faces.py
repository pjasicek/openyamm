"""Faces around the throat seam of 'Body' with their normals (a fold shows as normals pointing back). Args: blend"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.normal_update()
pl = bm.faces.layers.int['part']
n = 0
for f in bm.faces:
    c = f.calc_center_median()
    if c.y < -0.15 and 0.49 < c.z < 0.57 and abs(c.x) < 0.06 and f.normal.y > 0.2:
        n += 1
        print('BACK', f.index, 'part', f[pl], 'c', [round(x, 3) for x in c], 'n', [round(x, 2) for x in f.normal],
              'area %.6f' % f.calc_area(), [v.index for v in f.verts])
print('BACKFACES', n)
