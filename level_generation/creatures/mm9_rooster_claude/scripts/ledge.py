"""Throat ledge on 'Body': faces below the wattles that turn down (n.z < -0.5) in the neck front. Args: blend"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body'].data); bm.faces.ensure_lookup_table(); bm.normal_update()
pl = bm.faces.layers.int['part']
n = 0
for f in bm.faces:
    c = f.calc_center_median()
    if c.y < -0.1 and 0.47 < c.z < 0.6 and abs(c.x) < 0.09 and f[pl] != 2 and f.normal.z < -0.45:
        n += 1
        print('LEDGE', f.index, 'part', f[pl], [round(x, 3) for x in c], [round(x, 2) for x in f.normal], 'area %.6f' % f.calc_area())
print('LEDGES', n)
