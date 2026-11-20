"""Faces with rest positions, PartUV, set. Args: <uv blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
for m in list(body.modifiers): body.modifiers.remove(m)
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
uv = me.uv_layers['PartUV'].data
P = np.array([v.co[:] for v in me.vertices]); N = np.array([v.normal[:] for v in me.vertices])
fv = np.array([list(p.vertices) for p in me.polygons]); fu = np.array([[uv[l].uv[:] for l in p.loop_indices] for p in me.polygons])
np.savez(a[1], co=P[fv], nor=N[fv], uv=fu, mat=mat, part=fp)
print('DUMP', fv.shape)
