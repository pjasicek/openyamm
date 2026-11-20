"""Smooth the two low stubs the fin opening left behind the gills (where Meshy's pectoral pieces met the flank): a
Laplacian relax of the 'Body' surface vertices within 18 mm of (|x|, y=-0.098, z=0.071), feathered, on both sides. No
topology or UV change. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; me = body.data
P = np.array([tuple(v.co) for v in me.vertices])
nbr = [[] for _ in P]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
piece = np.zeros(len(P), int); pa = me.attributes['piece']
for p in me.polygons:
    for v in p.vertices:
        piece[v] = max(piece[v], pa.data[p.index].value)
d = np.hypot((P[:, 1] + 0.098) / 0.016, (P[:, 2] - 0.071) / 0.020)
w = np.clip(1.5 - d, 0, 1) * (piece == 0) * (np.abs(P[:, 0]) > 0.005)
print('STUB verts', int((w > 0).sum()))
for _ in range(14):
    avg = np.array([P[n].mean(0) if n else P[i] for i, n in enumerate(nbr)])
    P = P + (avg - P) * (0.6 * w)[:, None]
for i, v in enumerate(me.vertices):
    v.co = P[i]
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
