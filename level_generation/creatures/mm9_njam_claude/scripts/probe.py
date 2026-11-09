import bpy, sys, bmesh
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
bm = bmesh.new(); bm.from_mesh(me); lay = bm.faces.layers.int['part']
print('PROBE boundary near chest', sum(1 for e in bm.edges if e.is_boundary and abs(e.verts[0].co.x) < 0.09 and 0.33 < e.verts[0].co.z < 0.62 and e.verts[0].co.y < 0))
for z0, x0 in ((0.56, 0.03), (0.415, 0.0)):
    fs = [f for f in bm.faces if abs(f.calc_center_median().z - z0) < 0.04 and abs(abs(f.calc_center_median().x) - x0) < 0.02 and f.calc_center_median().y < 0]
    print('PROBE', z0, [(f[lay], [round(c, 2) for c in f.normal], [round(c, 3) for c in f.calc_center_median()], round(f.calc_area() * 1e4, 2)) for f in fs][:14])
