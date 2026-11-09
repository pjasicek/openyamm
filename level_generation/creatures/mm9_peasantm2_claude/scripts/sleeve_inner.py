"""Bell sleeves are double-walled (Meshy closed them with an inner wall). The procedural arm bands weighted the two walls apart, so the
inner wall pushed out through the outer one in the lowered-arm poses. Every inner-wall vertex (normal toward the arm axis) takes the
weights of the nearest outer-wall vertex. Weights only: UVs, positions and loops unchanged. Args: <in blend> <out blend>"""
import bpy, sys, json, os
import numpy as np
from mathutils.kdtree import KDTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
P = np.array([v.co[:] for v in me.vertices]); N = np.array([v.normal[:] for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
inner = np.zeros(len(P), bool); outer = np.zeros(len(P), bool)
for s in 'LR':
    a, b, c = (J[f'Bip01 {s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand'))
    best = np.full(len(P), 9.0); dot = np.zeros(len(P))
    for p0, p1 in ((a, b), (b, c)):
        L = np.linalg.norm(p1 - p0); d = (p1 - p0) / L; t = np.clip((P - p0) @ d, 0, L)
        r = P - (p0 + np.outer(t, d)); rl = np.linalg.norm(r, axis=1)
        m = rl < best; best[m] = rl[m]; dot[m] = ((N * r).sum(1) / (rl + 1e-9))[m]
    near = (pa == 1) & (best < 0.16) & (np.sign(P[:, 0]) == np.sign(a[0])) & (np.abs(P[:, 0]) > 0.24)
    inner |= near & (dot < -0.1); outer |= near & (dot > 0.1)
oi = np.nonzero(outer)[0]; kd = KDTree(len(oi))
for k, i in enumerate(oi): kd.insert(P[i], k)
kd.balance()
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(P), len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
moved = []
for i in np.nonzero(inner)[0]:
    co, k, dist = kd.find(P[i]); j = oi[k]; W[i] = W[j]; moved.append(dist)
for gi, g in enumerate(body.vertex_groups):
    g.remove(list(range(len(P))))
    for i in np.nonzero(W[:, gi] > 0)[0]: g.add([int(i)], float(W[i, gi]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('INNER verts', int(inner.sum()), 'outer', int(outer.sum()), 'nearest dist mm p50/max', round(float(np.median(moved)) * 1000, 1), round(float(np.max(moved)) * 1000, 1))
