"""m222 weight rules, by garment (scripts/garments.py 'garment' attribute); bar1's armour rules + natm's strip rule:
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/neck free of the shoulders.
             The long hair slab is part of this shell (Meshy's spine/neck/head weights are kept); skin that hangs
             behind the back (the hair) drops arm weight.
1 helmet     helmet shell and eyes rigid on B_Head.
2 guard      right shoulder guard: per-vertex copy of the skin under it (4 nearest, inverse distance), arm share capped
             at 0.5 (excess to the clavicle) so the plate rides the shoulder instead of the biceps.
3 panels     the gold front panels: pelvis at the belt -> the thigh on the panel's side at the hem (one side per panel).
4 trim       neck trim and clasp: copy of the skin under it, no arm weight.
5 links      belt chain links rigid on B_Pelvis.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
J = lambda n: np.array(rig.data.bones[n].head_local)
idx = lambda keys: [gi[n] for n in names if any(k in n for k in keys)]
ARM = {s: idx((f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'B_{s}_Finger')) for s in 'LR'}
ARMS = ARM['L'] + ARM['R']
PEL = gi['B_Pelvis']
skin = np.where(gv == 0)[0]

# skin rules ---------------------------------------------------------------------------------------------------------
moved = 0
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    for i in skin:
        m = (co[i] - sh) @ d
        if m < 0 and Wt[i, ua] > 0:
            keep = max(0.0, 1.0 + m / 0.07)
            dw = Wt[i, ua] * (1 - keep)
            Wt[i, ua] -= dw; Wt[i, cv] += dw; moved += dw > 1e-3
print('RULE skin shoulder fade: vertices changed', moved)
jz = J('B_Head')[2] - 0.02; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm', 'UpperArmTwist'))]
neck_moved = 0
for i in skin:
    fz = float(np.clip((co[i, 2] - (jz - 0.03)) / 0.03, 0, 1))
    if fz <= 0:
        continue
    r = fz * (1 - float(np.clip((abs(co[i, 0] - ax_x) - 0.07) / 0.07, 0, 1)))
    dw = Wt[i, SH].sum() * r
    if dw > 1e-4:
        Wt[i, SH] *= (1 - r); Wt[i, gi['B_Head'] if co[i, 2] > jz else gi['B_Neck']] += dw; neck_moved += 1
print('RULE skin jaw free of the shoulders: vertices changed', neck_moved)
# hair slab: P00 skin behind the back (y beyond the shoulder blades) between the shoulders: no arm weight
back_y = J('B_Spine2')[1] + 0.06
hair = [i for i in np.where(pv == 0)[0] if co[i, 1] > back_y and abs(co[i, 0]) < 0.13 and co[i, 2] > J('B_Spine1')[2]]
a = Wt[hair][:, ARMS].sum(1)
Wt[np.ix_(hair, ARMS)] = 0
Wt[hair, gi['B_Spine2']] += a
print('RULE hair slab: vertices', len(hair), 'arm weight moved to the chest, max', round(float(a.max()) if len(a) else 0, 3))

kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()


def copy(i):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()


count = {}
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    if g == 1:
        new = np.zeros((len(ids), len(names))); new[:, gi['B_Head']] = 1
    elif g == 2:
        C = np.array([copy(i) for i in ids])
        for s in 'LR':
            a = C[:, ARM[s]].sum(1); over = np.clip(a - 0.5, 0, None)
            sc = np.where(a > 1e-9, (a - over) / np.maximum(a, 1e-9), 1)
            C[:, ARM[s]] *= sc[:, None]; C[:, gi[f'B_{s}_Clavicle']] += over
        new = C
    elif g == 3:
        z = co[ids][:, 2]
        top, bot = z.max(), z.min()
        a = np.clip((top - 0.03 - z) / max(top - 0.03 - bot, 1e-3), 0, 1)
        side = 'L' if co[ids][:, 0].mean() > 0 else 'R'
        new = np.zeros((len(ids), len(names))); new[:, PEL] = 1 - a; new[:, gi[f'B_{side}_Thigh']] = a
        print('RULE panel piece', p, 'pelvis -> B_' + side + '_Thigh over', round(float(top - bot) * 100, 1), 'cm')
    elif g == 4:
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0
        new = C
    else:
        new = np.zeros((len(ids), len(names))); new[:, PEL] = 1
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    count[g] = count.get(g, 0) + 1
print('RULE pieces per garment', count)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
