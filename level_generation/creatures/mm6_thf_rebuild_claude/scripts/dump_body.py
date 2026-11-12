"""Dump Body (world coords, triangles, face part, optional face attribute 'hand') and MM9_Rig joints to npz. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
SRC, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
o = bpy.data.objects['Body']; me = o.data
rig = bpy.data.objects.get('MM9_Rig')
V = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
F, FP = [], []
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
for p in me.polygons:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1):
        F.append([vs[0], vs[k], vs[k + 1]]); FP.append(fp[p.index])
jn, jp = [], []
if rig:
    jn = [b.name for b in rig.data.bones]; jp = [tuple(rig.matrix_world @ b.head_local) for b in rig.data.bones]
np.savez(OUT, V=V, F=np.array(F), part=np.array(FP), jn=np.array(jn), jp=np.array(jp))
print('DUMP', len(V), len(F))
