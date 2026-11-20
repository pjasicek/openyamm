"""Corner UVs of the frozen layout for the compose step: work/uv_dump.npz with tri (faces x 3 vertex ids), uvc (faces x 3 x 2, PartUV),
mat (0 body, 1 head), part, co (bind positions). Args: <uv blend> <out npz>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
n = len(me.polygons)
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
pu = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers['PartUV'].data.foreach_get('uv', pu); pu = pu.reshape(-1, 2)
li = np.array([list(p.loop_indices) for p in me.polygons], np.int32)
mat = np.zeros(n, np.int32); me.attributes['mat'].data.foreach_get('value', mat)
part = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', part)
co = np.array([v.co[:] for v in me.vertices], np.float32)
np.savez(OUT, tri=tri, uvc=pu[li], mat=mat, part=part, co=co)
print('DUMPUV', n)
