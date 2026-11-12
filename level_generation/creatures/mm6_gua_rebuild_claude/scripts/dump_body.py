"""Body (rest, evaluated without armature) to npz: V, F (triangles), part, garm. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
SRC, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
b = bpy.data.objects['Body']; me = b.data
V = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
F = []; P = []; G = []
pa = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', pa)
ga = np.zeros(len(me.polygons), int)
if 'garm' in me.attributes: me.attributes['garm'].data.foreach_get('value', ga)
for p in me.polygons:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1):
        F.append([vs[0], vs[k], vs[k + 1]]); P.append(pa[p.index]); G.append(ga[p.index])
np.savez(OUT, V=V, F=np.array(F), part=np.array(P), garm=np.array(G))
print('DUMPB', len(V), len(F))
