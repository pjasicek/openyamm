import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pc = np.array([d.value for d in me.attributes['piece'].data])
co = co[pc == 0]
print('BB', co.min(0).round(3), co.max(0).round(3))
for y0 in np.arange(-0.2, 0.3, 0.025):
    m = (co[:, 1] >= y0) & (co[:, 1] < y0 + 0.025) & (np.abs(co[:, 0]) < 0.015)
    if m.any(): print('MID y %.3f zmin %.3f zmax %.3f' % (y0, co[m, 2].min(), co[m, 2].max()))
