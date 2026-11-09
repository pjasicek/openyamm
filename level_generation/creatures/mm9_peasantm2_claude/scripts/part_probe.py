import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body'].data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
c = np.array([p.center[:] for p in me.polygons])
for k in (7, 9, 10):
    m = fp == k
    print('PP part', k, int(m.sum()), 'x range', c[m, 0].min().round(3), c[m, 0].max().round(3), 'z', c[m, 2].min().round(3), c[m, 2].max().round(3), 'faces |x|>0.2:', int((m & (np.abs(c[:, 0]) > 0.2)).sum()))
