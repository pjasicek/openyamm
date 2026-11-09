"""Weights on the frozen mesh (UVs and paints stay): where the collapse gate found folds. Knee pivot further toward the back of the leg, ankle half-joint helpers Foot_h, relax on the neck band, shoulders and armpits, elbows, knee backs. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
B = 'Bip01 '
KNEE = float(sys.argv[sys.argv.index('--') + 3]) if len(sys.argv) > sys.argv.index('--') + 3 else 0.02
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted().to_3x3()
for s in 'LR':
    e = eb[f'{B}{s} Calf']; v = Mi @ Vector((0, KNEE, 0)); e.head += v; e.tail += v
    h = eb[f'{B}{s} Calf_h']; h.head += v; h.tail += v
    f = eb[f'{B}{s} Foot']; n = eb.new(f'{B}{s} Foot_h'); n.head = f.head; n.tail = f.tail; n.roll = f.roll; n.parent = f.parent; n.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
for s in 'LR': body.vertex_groups.new(name=f'{B}{s} Foot_h')
names = [g.name for g in body.vertex_groups]; idx = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
skin = np.isin(pa, (1, 5, 6, 20))
def relax(mask, its, k=0.5):
    ids = np.nonzero(mask & skin)[0]
    for _ in range(its):
        W[ids] = (1 - k) * W[ids] + k * np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
    print('RELAX', len(ids), its)
# ankle helpers: the boot's band between calf and foot
for s in 'LR':
    c, f, h = idx[f'{B}{s} Calf'], idx[f'{B}{s} Foot'], idx[f'{B}{s} Foot_h']
    ch = idx.get(f'{B}{s} Calf_h')
    wc = W[:, c]; wf = W[:, f]; tot = wc + wf; m = (wc > 1e-3) & (wf > 1e-3) & (pa == 6)
    t = wf[m] / tot[m]
    W[m, c] = tot[m] * np.maximum(1 - 2 * t, 0); W[m, f] = tot[m] * np.maximum(2 * t - 1, 0); W[m, h] = tot[m] * (1 - np.abs(2 * t - 1))
    print('FOOT_H', s, int(m.sum()))
Cn = np.array([0.0, 0.0, 0.70]); Nk = np.array([0.0, -0.12, 0.99]); Nk /= np.linalg.norm(Nk)
hh = (P - Cn) @ Nk
neck = (np.abs(hh) < 0.055) & (pa == 20) & (np.hypot(P[:, 0], P[:, 1] - 0.011) < 0.083)
relax(neck, 6)
for s in 'LR':
    relax((np.linalg.norm(P - J[f'{B}{s} UpperArm'], axis=1) < 0.15) & (pa == 1), 8)
    relax((np.linalg.norm(P - J[f'{B}{s} Forearm'], axis=1) < 0.11) & (pa == 1), 6)
    relax((np.linalg.norm(P - J[f'{B}{s} Calf'], axis=1) < 0.11) & (pa == 5), 4)
    relax((np.linalg.norm(P - J[f'{B}{s} Foot'], axis=1) < 0.13) & (pa == 6), 8)
# the skirt hangs and goes with the legs: toward the hem part of each vertex follows the thigh on its side, so a hinge only has to lift what a thigh still reaches
sk_ = np.nonzero(pa == 7)[0]
kk = 0.72 * np.clip((0.06 - P[sk_, 2]) / 0.37, 0, 1) ** 1.1
sL = np.clip((P[sk_, 0] + 0.15) / 0.30, 0, 1); sL = sL * sL * (3 - 2 * sL)
W[sk_] *= (1 - kk)[:, None]
W[sk_, idx[B + 'L Thigh']] += kk * sL; W[sk_, idx[B + 'R Thigh']] += kk * (1 - sL)
order = np.argsort(-W, axis=1)
for i in sk_:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for i in np.nonzero(skin)[0]:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for g in body.vertex_groups:
    j = g.index
    g.remove(list(range(n)))
    for i in np.nonzero(W[:, j])[0]: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('REWEIGHT done')
