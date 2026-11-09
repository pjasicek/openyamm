"""Head set triangles (face attribute mat == 2): rest positions, smooth normals, HeadUV, part (13 eyes). Args: <uv blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
for m in list(body.modifiers): body.modifiers.remove(m)
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
uv = me.uv_layers['HeadUV'].data
P = np.array([v.co[:] for v in me.vertices]); N = np.array([v.normal[:] for v in me.vertices])
fv = []; fu = []
for p in me.polygons:
    if mat[p.index] != 2: continue
    fv.append(list(p.vertices)); fu.append([uv[l].uv[:] for l in p.loop_indices])
fv = np.array(fv); fu = np.array(fu)
np.savez(a[1], co=P[fv], nor=N[fv], uv=fu, part=pa[fv].max(1))
print('HEADFACES', len(fv))
