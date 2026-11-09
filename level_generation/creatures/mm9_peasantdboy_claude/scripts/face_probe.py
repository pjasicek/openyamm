"""Front profile of the head shell: per 5 mm z slice the front-most y at |x| < 0.01 and the face half-width.
Args: <blend>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
vs = sorted({v for p in me.polygons if hd[p.index] for v in p.vertices})
co = np.array([tuple(b.matrix_world @ me.vertices[i].co) for i in vs])
for z in np.arange(co[:, 2].min(), co[:, 2].max(), 0.01):
    m = (np.abs(co[:, 2] - z) < 0.005)
    c = co[m & (np.abs(co[:, 0]) < 0.01)]
    f = co[m & (co[:, 1] < (c[:, 1].min() + 0.03 if len(c) else 0))]
    print('PROBE z %.3f front_y %s halfw %.3f' % (z, '%.3f' % c[:, 1].min() if len(c) else '-', np.abs(f[:, 0]).max() if len(f) else 0))
