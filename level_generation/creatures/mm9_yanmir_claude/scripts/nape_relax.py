"""The hair's lower rim on the mantle folds when MM9 turns or throws back the head (collapse gate: head 98 in Fidget2, 103 in
StartDie at the nape and the hair's side rims). The weights over a taller band round the back and sides of the neck (hair rim,
nape, mantle collar; not the beard, face or chin) are relaxed again, so the head's turn spreads over 10-12 cm instead of 4-5.
Writes <out>. Args: <in blend> <out blend> [iterations]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; IT = int(a[2]) if len(a) > 2 else 24
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
names = [g.name for g in body.vertex_groups]
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    x, y = e.vertices; nbr[x].append(y); nbr[y].append(x)
m = (pa == 0) & (P[:, 1] > -0.03) & (P[:, 2] > 0.84) & (P[:, 2] < 1.04) & (np.abs(P[:, 0]) < 0.26)
ids = np.nonzero(m)[0]
for _ in range(IT):
    W[ids] = 0.5 * W[ids] + 0.5 * np.array([W[nbr[i]].mean(0) for i in ids])
order = np.argsort(-W, axis=1)
for i in ids:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for j, nm in enumerate(names):
    g = body.vertex_groups[nm]
    g.remove([int(i) for i in ids])
    for i in ids:
        if W[i, j] > 0: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NAPE relaxed', len(ids), IT)
