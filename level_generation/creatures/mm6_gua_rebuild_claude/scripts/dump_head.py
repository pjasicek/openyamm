"""Head faces of the master for project_heads.py: positions, smooth normals, HeadUV, garment per corner. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']; me = o.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
pt = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', pt)
uv = me.uv_layers['HeadUV'].data
me.calc_loop_triangles() if False else None
P, N, U, F = [], [], [], []
vn = np.zeros((len(me.vertices), 3))
for p in me.polygons:
    for v in p.vertices: vn[v] += np.array(p.normal) * p.area
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)
for p in me.polygons:
    if not hd[p.index]: continue
    P.append([tuple(me.vertices[v].co) for v in p.vertices]); N.append([vn[v] for v in p.vertices])
    U.append([tuple(uv[l].uv) for l in p.loop_indices]); F.append(pt[p.index])
np.savez(a[1], p=np.array(P), n=np.array(N), u=np.array(U), part=np.array(F))
print('DUMPED', len(P))
