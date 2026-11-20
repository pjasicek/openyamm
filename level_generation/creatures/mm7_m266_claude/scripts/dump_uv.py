"""Dump UV triangles per face part (0 body, k head k) and rest-pose positions for numpy compose.
Args: -- <blend> <out npz>"""
import bpy, sys, os
import numpy as np
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
me.calc_loop_triangles()
uv = me.uv_layers['UVMap'].data
T = me.loop_triangles
tri_uv = np.array([[tuple(uv[l].uv) for l in t.loops] for t in T], np.float32)
tri_co = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in T], np.float32)
tri_part = np.array([part[t.polygon_index] for t in T], np.int32)
np.savez(os.path.abspath(out), uv=tri_uv, co=tri_co, part=tri_part)
print('DUMPUV', len(T))
