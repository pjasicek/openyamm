"""Weight repairs on the UV-mapped pig (same mesh and UVs). Args: <in blend> <out blend> <report json>

1. Midline: MM9's skin gives the chest and hip sides to the leg roots, so left and right roots met on the belly and
   tiny mid-plane edges tore 7 x in the walk. Leg-root weights fade into the spine towards x = 0 (wolf lesson), over
   MID_X, on the chest (XspineC) and hips (XspineA).
2. Ears: flap vertices the thickness test missed (beyond the head's width) keep head weights and stretched 8 x
   against their neighbours when the flap turned. Past EAR_X everything on the ear side is on the ear hinge.
"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
MID_X = 0.03
EAR_X = 0.07
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
names = [g.name for g in body.vertex_groups]
idx = {n: i for i, n in enumerate(names)}
n = len(me.vertices)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
P = np.array([tuple(v.co) for v in me.vertices])
FRONT = [b for b in ('Xftpiv', 'Xftleg', 'Xftlower', 'Xftpiv01', 'Xftleg01', 'Xftlower01') if b in idx]
BACK = [b for b in ('Xbkpivot', 'Xbkleg', 'Xbklower', 'Xbkpivot01', 'Xbkleg01', 'Xbklower01') if b in idx]
x = np.clip(np.abs(P[:, 0]) / MID_X, 0, 1)
keep = x * x * (3 - 2 * x)
for grp, to in ((FRONT, 'XspineC'), (BACK, 'XspineA')):
    for b in grp:
        moved = W[:, idx[b]] * (1 - keep)
        W[:, idx[to]] += moved
        W[:, idx[b]] -= moved
head = W[:, [idx[b] for b in ('Xhead', 'Xnose') if b in idx]].sum(1)
c = 0
for b, sgn in (('EarRoot', -1), ('EarRoot01', 1)):
    m = (np.sign(P[:, 0]) == sgn) & (np.abs(P[:, 0]) > EAR_X) & (P[:, 1] < -0.13) & (P[:, 2] > 0.19) & (head + W[:, idx[b]] > 0.5)
    W[m] = 0
    W[m, idx[b]] = 1
    c += int(m.sum())
W = W / W.sum(1, keepdims=True)
for g in list(body.vertex_groups):
    pass
for i in range(n):
    for j in range(len(names)):
        if W[i, j] > 1e-4:
            body.vertex_groups[j].add([i], float(W[i, j]), 'REPLACE')
        else:
            body.vertex_groups[j].remove([i])
rep = {'ear_verts': c, 'midline_verts': int((keep < 1).sum())}
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WEIGHTS', rep)
