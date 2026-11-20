"""Vertex positions and UVs of two blends' Body meshes must match (a weights-only fix on the painted layout)."""
import bpy, sys
import numpy as np
a, b = sys.argv[sys.argv.index('--') + 1:]
def read(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    me = bpy.data.objects['Body'].data
    c = np.zeros(3 * len(me.vertices)); me.vertices.foreach_get('co', c)
    u = np.zeros(2 * len(me.loops)); me.uv_layers['UVMap'].data.foreach_get('uv', u)
    return c.reshape(-1, 3), u
ca, ua = read(a); cb, ub = read(b)
print('SAME_MESH max vertex move', float(np.abs(ca - cb).max()), 'max uv diff', float(np.abs(ua - ub).max()), len(ca), len(cb))
