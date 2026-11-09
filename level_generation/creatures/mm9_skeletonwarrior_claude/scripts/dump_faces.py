"""Per-face UV triangles and part ids of the master, for the region masks. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
n = len(me.polygons)
ub = np.zeros(len(me.loops) * 2, np.float32); uh = ub.copy()
me.uv_layers['UVMap'].data.foreach_get('uv', ub); me.uv_layers['HeadUV'].data.foreach_get('uv', uh)
v = np.array([p.vertices[:] for p in me.polygons]); li = np.array([p.loop_indices[:] for p in me.polygons])
pid = np.zeros(len(me.vertices), np.int32); me.attributes['pid'].data.foreach_get('value', pid)
get = lambda k: (lambda x: (me.attributes[k].data.foreach_get('value', x), x)[1])(np.zeros(n, np.int32))
np.savez(a[1], ub=ub.reshape(-1, 2)[li], uh=uh.reshape(-1, 2)[li], pid=pid[v[:, 0]], head=get('head'), lining=get('lining'), scim=get('scim'))
print('DUMP', n)
