"""Half-rotation helper bones (cat and Mummy lessons): the skin over a joint follows an arc. Each helper is keyed half way by clips (half_keys). Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
B = 'Bip01 '
HELP = (('L Thigh', ('Spine',)), ('R Thigh', ('Spine',)), ('L Calf', ('L Thigh',)), ('R Calf', ('R Thigh',)), ('L Forearm', ('L UpperArm',)), ('R Forearm', ('R UpperArm',)),
        ('L UpperArm', ('L Clavicle', 'Spine3')), ('R UpperArm', ('R Clavicle', 'Spine3')), ('Head', ('Neck',)), ('Neck', ('Spine3',)), ('L Foot', ('L Calf',)), ('R Foot', ('R Calf',)))
parents = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for c, ps in HELP:
    h = eb.new(B + c + '_h'); t = eb[B + c]
    h.head = t.head; h.tail = t.tail; h.roll = t.roll; h.parent = eb[parents[B + c]]; h.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(body.vertex_groups):
    if g.name.startswith('MP_') or g.name not in rig.data.bones: body.vertex_groups.remove(g)
names = [g.name for g in body.vertex_groups]
for c, _ in HELP: names.append(B + c + '_h'); body.vertex_groups.new(name=B + c + '_h')
idx = {n: i for i, n in enumerate(names)}
n = len(me.vertices)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp); pa = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
skin = np.isin(pa, (1, 5, 6, 8, 20))
for c, ps in HELP:
    ci = idx[B + c]; pi = [idx[B + p] for p in ps if B + p in idx]; hi = idx[B + c + '_h']
    wc = W[:, ci]; wp = W[:, pi].sum(1); tot = wc + wp
    m = (wc > 1e-3) & (wp > 1e-3) & skin
    t = wc[m] / tot[m]
    scale = np.maximum(1 - 2 * t, 0)
    for p in pi: W[m, p] = W[m, p] * scale
    W[m, ci] = tot[m] * np.maximum(2 * t - 1, 0)
    W[m, hi] = tot[m] * (1 - np.abs(2 * t - 1))
# relax the bands where the collapse gate found folds (mm9_highwayman_claude/scripts/reweight.py)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
P = np.array([v.co[:] for v in me.vertices])
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
def relax(mask, its, k=0.5):
    ids = np.nonzero(mask & skin)[0]
    for _ in range(its):
        W[ids] = (1 - k) * W[ids] + k * np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
    print('RELAX', len(ids), its)
relax((np.abs(P[:, 2] - 0.70) < 0.06) & (np.hypot(P[:, 0], P[:, 1] - 0.05) < 0.11) & (pa == 20), 6)
for s in 'LR':
    relax((np.linalg.norm(P - J[f'{B}{s} UpperArm'], axis=1) < 0.21) & (pa != 8), 12)
    relax(np.linalg.norm(P - J[f'{B}{s} Forearm'], axis=1) < 0.10, 4)
    relax((np.linalg.norm(P - J[f'{B}{s} Calf'], axis=1) < 0.12) & (pa == 5), 4)
    relax(np.linalg.norm(P - J[f'{B}{s} Foot'], axis=1) < 0.13, 6)
    relax((np.linalg.norm(P - J[f'{B}{s} Thigh'], axis=1) < 0.16) & (pa == 5), 6)
relax(pa == 8, 14)                        # the mantle moves as one stiff cape
# the legs' hidden top ring stays rigid on the Spine, as the belt does: MM9's thighs hang from the Spine and the two parts must not part
top = (pa == 5) & (P[:, 2] > 0.09)
k = np.clip((P[top, 2] - 0.09) / 0.05, 0, 1); k = k * k * (3 - 2 * k)
W[top] *= (1 - k)[:, None]; W[top, idx[B + 'Spine']] += k
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for g in body.vertex_groups:
    j = idx[g.name]
    g.remove(list(range(n)))
    ids = np.nonzero(W[:, j])[0]
    for i in ids: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HELPERS', len(HELP), 'bones', len(rig.data.bones))
