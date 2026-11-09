"""Neck/collar geometry of the cleaned body: collar ring and old neck centre per height. Args: <clean blend>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
for z in (0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74):
    m = (np.abs(P[:, 2] - z) < 0.01) & (vp == 1) & (np.abs(P[:, 0]) < 0.12)
    n = (np.abs(P[:, 2] - z) < 0.01) & (vp == 2)
    print('RING', z, 'collar', P[m].min(0).round(3).tolist() if m.any() else '', P[m].max(0).round(3).tolist() if m.any() else '', 'neck', P[n].min(0).round(3).tolist() if n.any() else '', P[n].max(0).round(3).tolist() if n.any() else '')
