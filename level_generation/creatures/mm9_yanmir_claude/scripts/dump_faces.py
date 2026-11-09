"""Face positions and UVs per set for tier masks. Args: <uv blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
for m in list(body.modifiers): body.modifiers.remove(m)
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
P = np.array([v.co[:] for v in me.vertices]); uv = me.uv_layers['PartUV'].data
out = {0: ([], [], []), 2: ([], [], [])}
for p in me.polygons:
    o = out[int(mat[p.index])]; o[0].append(P[list(p.vertices)]); o[1].append([uv[l].uv[:] for l in p.loop_indices]); o[2].append(pa[list(p.vertices)].max())
np.savez(a[1], bc=np.array(out[0][0]), bu=np.array(out[0][1]), bp=np.array(out[0][2]), hc=np.array(out[2][0]), hu=np.array(out[2][1]), hp=np.array(out[2][2]))
print('DUMPF', len(out[0][0]), len(out[2][0]))
