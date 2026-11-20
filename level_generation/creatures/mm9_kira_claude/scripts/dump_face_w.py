"""Dump the face-skin and head-set vertices with their bone weights (analysis for face_rigid.py). Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
print('DUMP body mw', [list(r) for r in body.matrix_world], 'rig mw', [list(r) for r in rig.matrix_world])
n = len(me.vertices); names = [g.name for g in body.vertex_groups]
W = np.zeros((n, len(names)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp); pa = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
P = np.array([v.co[:] for v in me.vertices]); N = np.array([v.normal[:] for v in me.vertices])
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
T = {b.name: np.array(rig.matrix_world @ b.tail_local) for b in rig.data.bones}
E = np.array([e.vertices[:] for e in me.edges])
Fc = [list(p.vertices) for p in me.polygons]; fl = np.array([len(f) for f in Fc]); Ff = np.array([v for f in Fc for v in f])
hand = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', hand)
np.savez(OUT, P=P, N=N, W=W, names=np.array(names), pa=pa, E=E, jn=np.array(list(J)), jh=np.array(list(J.values())), jt=np.array(list(T.values())), fl=fl, Ff=Ff, fp=fp, hand=hand)
print('DUMP done', n, len(names))
