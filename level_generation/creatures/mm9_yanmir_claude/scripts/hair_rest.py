"""The long hair rests on the back and the shoulders: its lower part follows the neck and the upper spine more than the head, as
hair does (collapse gate: the hair rim, rigid on Head, folded into the mantle when MM9 throws the head back or turns it: head
80-124 in StartDie, Death, Death2, 68 in Fidget2 after the twist cap). Behind the ears (y > 0.0) and below z 1.07, the head's share
(Head, Head_h, Ponytail1) eases from all at z 1.07 to HMIN at z 0.90; the rest goes to Neck and Spine2 (half each).
Args: <in blend> <out blend> [hmin]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; HMIN = float(a[2]) if len(a) > 2 else 0.25
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
names = [g.name for g in body.vertex_groups]; ix = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
def sstep(x, a_, b_):
    t = np.clip((x - a_) / (b_ - a_), 0, 1); return t * t * (3 - 2 * t)
H = [ix[k] for k in ('Bip01 Head', 'Bip01 Head_h', 'Bip01 Ponytail1') if k in ix]
hs = W[:, H].sum(1)
back = sstep(P[:, 1], -0.02, 0.04) * (1 - sstep(np.abs(P[:, 0]), 0.24, 0.30))
m = (pa == 0) & (back > 0) & (P[:, 2] > 0.86) & (P[:, 2] < 1.08) & (hs > 0.05)
f = HMIN + (1 - HMIN) * sstep(P[:, 2], 0.90, 1.07)
keep = 1 - back * (1 - f)                         # the head's share left
ids = np.nonzero(m)[0]
for i in ids:
    take = hs[i] * (1 - keep[i])
    W[i, H] *= keep[i]
    W[i, ix['Bip01 Neck']] += take * 0.5; W[i, ix['Bip01 Spine2']] += take * 0.5
order = np.argsort(-W, axis=1)
for i in ids:
    k4 = order[i, :4]; row = np.zeros(len(names)); row[k4] = W[i, k4]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for j, nm in enumerate(names):
    g = body.vertex_groups[nm]; g.remove([int(i) for i in ids])
    for i in ids:
        if W[i, j] > 0: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HAIR rest', len(ids), 'mean head share before', round(float(hs[ids].mean()), 3), 'after', round(float(W[ids][:, H].sum(1).mean()), 3))
