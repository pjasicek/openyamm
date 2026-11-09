"""Compare the UV layer of two blends' 'Body' (same topology). Args: -- <a.blend> <b.blend>"""
import bpy, sys, os
import numpy as np
a, b = sys.argv[sys.argv.index('--') + 1:]
def uvs(p):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p)); me = bpy.data.objects['Body'].data
    u = np.empty(len(me.loops) * 2); me.uv_layers['UVMap'].data.foreach_get('uv', u); return u
ua, ub = uvs(a), uvs(b)
print('UVCOMPARE loops', len(ua) // 2, 'max diff', float(np.abs(ua - ub).max()) if len(ua) == len(ub) else 'size mismatch')
