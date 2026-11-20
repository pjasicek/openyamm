"""Weights on the frozen mesh (UVs and paints stay): the waist relaxes where the spine bends. Skin only. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
names = [g.name for g in body.vertex_groups]; idx = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
skin = pa == 0
def relax(mask, its, k=0.5):
    ids = np.nonzero(mask & skin)[0]
    for _ in range(its):
        W[ids] = (1 - k) * W[ids] + k * np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
    print('RELAX', len(ids), its)
relax((P[:, 2] > -0.28) & (P[:, 2] < 0.4) & (np.abs(P[:, 0]) < 0.34), 8)
order = np.argsort(-W, axis=1)
for i in np.nonzero(skin)[0]:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for j, nm in enumerate(names):
    g = body.vertex_groups[nm]
    g.remove(list(range(n)))
    for i in np.nonzero(W[:, j])[0]: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('REWEIGHT done')
