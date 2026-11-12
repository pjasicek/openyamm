"""Rest-pose triangles with UVMap and HeadUV per corner, face part/garm/head/hand -> npz. Args: <blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
SRC, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
b = bpy.data.objects['Body']; me = b.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces)
uv = bm.loops.layers.uv['UVMap']; hu = bm.loops.layers.uv.get('HeadUV')
L = {k: bm.faces.layers.int.get(k) for k in ('part', 'garm', 'head', 'hand')}
P, UV, HU, A = [], [], [], {k: [] for k in L}
for f in bm.faces:
    P.append([tuple(l.vert.co) for l in f.loops]); UV.append([tuple(l[uv].uv) for l in f.loops])
    HU.append([tuple(l[hu].uv) for l in f.loops] if hu else [(0, 0)] * 3)
    for k, lay in L.items(): A[k].append(f[lay] if lay else 0)
np.savez(OUT, P=np.array(P), UV=np.array(UV), HU=np.array(HU), **{k: np.array(v) for k, v in A.items()})
print('DUMPUV', len(P))
