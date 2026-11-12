"""Weights only, after the paint: Laplacian smoothing of the skin weights of chosen parts inside a box (the hood's collar: a long Head -> Neck ->
Spine3 ramp, as the Guard's coif needed). Every bone's weight is averaged with the vertex neighbours PASSES times, then top 4 kept, normalised.
Args: <in blend> <out blend> <parts,comma> <xmax> <zmin> <zmax> <passes>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[:2]; PARTS = [int(x) for x in a[2].split(',')]; XMAX, ZMIN, ZMAX, PASSES = float(a[3]), float(a[4]), float(a[5]), int(a[6])
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
n = len(me.vertices); ng = len(body.vertex_groups)
W = np.zeros((n, ng))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
inpart = np.zeros(n, bool)
for p in me.polygons:
    if fp[p.index] in PARTS:
        for v in p.vertices: inpart[v] = True
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
sel = inpart & (np.abs(co[:, 0]) < XMAX) & (co[:, 2] > ZMIN) & (co[:, 2] < ZMAX)
nbr = [[] for _ in range(n)]
for e in me.edges:
    x, y = e.vertices
    if inpart[x] and inpart[y]: nbr[x].append(y); nbr[y].append(x)
for _ in range(PASSES):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W[sel] = 0.5 * W[sel] + 0.5 * avg[sel]
for i in np.nonzero(sel)[0]:
    o = np.argsort(-W[i]); row = np.zeros(ng); row[o[:4]] = W[i, o[:4]]; row[row < 0.02] = 0; W[i] = row / row.sum()
for g in body.vertex_groups:
    j = g.index; ids = np.nonzero(sel)[0]
    g.remove(ids.tolist())
    for i in ids:
        if W[i, j] > 0: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SMOOTH verts', int(sel.sum()), 'passes', PASSES)
