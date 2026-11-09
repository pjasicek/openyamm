"""Weights before the helpers: forearm-to-hand ramp over the wrist (the graft's stub had a step: a kink like a bracelet), head band widened, and a relax round every joint the gate names. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
for g in list(body.vertex_groups):
    if g.name.startswith('MP_') or g.name not in rig.data.bones: body.vertex_groups.remove(g)
have = [g.name for g in body.vertex_groups]
for b in rig.data.bones:
    if b.name not in have and b.use_deform: body.vertex_groups.new(name=b.name)
names = [g.name for g in body.vertex_groups]; idx = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
B = 'Bip01 '
skin = pa == 0
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
def relax(mask, its, k=0.5):
    ids = np.nonzero(mask & skin)[0]
    for _ in range(its):
        W[ids] = (1 - k) * W[ids] + k * np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
    print('RELAX', len(ids), its)
for s, sg in (('L', 1), ('R', -1)):
    E_, H_ = J[B + f'{s} Forearm'], J[B + f'{s} Hand']
    d = H_ - E_; L = np.linalg.norm(d); d = d / L
    al = (P - H_) @ d; rad = np.linalg.norm(P - H_ - np.outer(al, d), axis=1)
    m = skin & (np.sign(P[:, 0]) == sg) & (rad < 0.26) & (al > -0.1)
    t = sstep(al, -0.045, 0.075)
    W[m] = 0; W[m, idx[B + f'{s} Hand']] = t[m]; W[m, idx[B + f'{s} Forearm']] = 1 - t[m]
    print('WRIST', s, int(m.sum()))
C = np.array([0.0, 0.03, 0.76]); Nk = np.array([0.0, -0.25, 0.968]); Nk /= np.linalg.norm(Nk)
hh = (P - C) @ Nk
relax((hh > -0.1) & (hh < 0.06) & (np.abs(P[:, 0]) < 0.3) & (P[:, 1] > -0.32) & ~((P[:, 1] < -0.12) & (hh > 0.0)), 10)
for s in 'LR':
    relax(np.linalg.norm(P - J[B + f'{s} UpperArm'], axis=1) < 0.26, 10)
    relax(np.linalg.norm(P - J[B + f'{s} Forearm'], axis=1) < 0.15, 6)
    relax(np.linalg.norm(P - J[B + f'{s} Thigh'], axis=1) < 0.26, 8)
    relax(np.linalg.norm(P - J[B + f'{s} Calf'], axis=1) < 0.2, 8)
    relax(np.linalg.norm(P - J[B + f'{s} Foot'], axis=1) < 0.12, 4)
order = np.argsort(-W, axis=1)
for i in np.nonzero(skin)[0]:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for j, nm in enumerate(names):
    g = body.vertex_groups[nm]
    g.remove(list(range(n)))
    for i in np.nonzero(W[:, j])[0]: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('REWEIGHT done', len(names))
