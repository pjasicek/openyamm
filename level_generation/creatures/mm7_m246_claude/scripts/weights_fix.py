"""m246 weight rules, by garment (scripts/garments.py 'garment' attribute):
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/neck free of the shoulders.
1 head       crest, helmet, eyes, cheek pieces, goatee, helmet spikes rigid on B_Head.
2 panels     hip panels: pelvis at the strip's top -> the thigh at its hem, ONE left/right mixture per strip (gob2).
3 hair       copy of the skin under it (4 nearest, inverse distance), no arm weight.
1 crest      (piece 1) head at the root, blending to the skin under it toward the tip (70 % at the tip).
4 studs      spikes and studs: one uniform weight set per piece = the mean of the finished weights under it (so a stud
             rides its plate, twist bones included, without deforming).
5 vest       vest, strap, belt: copy of the skin, no arm weight.
6 plates     bracers, upper-arm plate, shin guards: copy of the skin as is (twist bones included).
7 pauldron   copy of the skin, arm share capped at 0.5 (excess to the clavicle; m222).
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
ARMS = idx(('UpperArm', 'Forearm', 'Hand', 'Finger'))
CLAV = idx(('Clavicle',))
PEL = gi['B_Pelvis']
skin = np.where(gv == 0)[0]
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
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
ARM = {s_: idx((f'B_{s_}_UpperArm', f'B_{s_}_Forearm', f'B_{s_}_Hand', f'B_{s_}_Finger')) for s_ in 'LR'}
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()


def copy(i, tree=kd, src=skin):
    hits = tree.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[src[h[1]] for h in hits]]).sum(0) / w.sum()


count = {}
for p in sorted(set(pv[(gv != 0) & (gv != 4)].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    if g == 1 and p == 1:
        # the long crest is a horsehair plume hanging down the back: rigid on the head at its root, its trailing part
        # blends toward the skin under it (up to 70 % at the tip) so a head tilt does not drive it into the back
        z = co[ids][:, 2]; zr, zt = z.max() - 0.12, z.min()
        a = 0.7 * np.clip((zr - z) / max(zr - zt, 1e-3), 0, 1)
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0
        C /= np.maximum(C.sum(1, keepdims=True), 1e-9)
        Cm = C[a > 0.35].mean(0); Cm /= Cm.sum()      # ONE target for the whole plume: a bend, no shear across it
        new = np.outer(a, Cm); new[:, gi['B_Head']] += 1 - a
        print('RULE crest piece', p, 'head -> skin under it, tip share', round(float(a.max()), 2))
    elif g == 1:
        new = np.zeros((len(ids), len(names))); new[:, gi['B_Head']] = 1
    elif g == 2:
        z = co[ids][:, 2]; top, bot = z.max(), z.min()
        a = np.clip((top - 0.03 - z) / max(top - 0.03 - bot, 1e-3), 0, 1)
        wl = float(np.clip(0.5 + co[ids][:, 0].mean() / 0.12, 0, 1))
        new = np.zeros((len(ids), len(names))); new[:, PEL] = 1 - a
        new[:, gi['B_L_Thigh']] = a * wl; new[:, gi['B_R_Thigh']] = a * (1 - wl)
        print('RULE strip piece', p, 'left share', round(wl, 2), 'over', round(float(top - bot) * 100, 1), 'cm')
    elif g == 3:   # hair: rides the shoulders it lies on (clavicles kept; zeroing them let shrugs push skin through it)
        new = np.array([copy(i) for i in ids]); new[:, ARMS] = 0
        # the per-vertex copy sheared the strands (3.8x edge stretch at rest pose motion): smooth the weights along the
        # hair's own edges (20 passes) so neighbouring strand vertices move together
        loc_ = {int(v): k for k, v in enumerate(ids)}
        nb = [[] for _ in ids]
        for e in me.edges:
            a_, b_ = e.vertices
            if a_ in loc_ and b_ in loc_:
                nb[loc_[a_]].append(loc_[b_]); nb[loc_[b_]].append(loc_[a_])
        for _ in range(int(os.environ.get('HAIR_SMOOTH', '20'))):
            new = np.array([0.5 * new[k] + 0.5 * new[n].mean(0) if n else new[k] for k, n in enumerate(nb)])
    elif g == 5:
        new = np.array([copy(i) for i in ids]); new[:, ARMS] = 0
    elif g == 6:
        new = np.array([copy(i) for i in ids])
    elif g == 7:
        C = np.array([copy(i) for i in ids])
        for s_ in 'LR':
            a = C[:, ARM[s_]].sum(1); over = np.clip(a - 0.5, 0, None)
            sc = np.where(a > 1e-9, (a - over) / np.maximum(a, 1e-9), 1)
            C[:, ARM[s_]] *= sc[:, None]; C[:, gi[f'B_{s_}_Clavicle']] += over
        new = C
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    count[g] = count.get(g, 0) + 1
# studs last: the mean of the finished weights of the nearest non-stud vertices (any garment but the head)
base = np.where((gv != 4) & (gv != 1))[0]
kd2 = KDTree(len(base))
for i, s in enumerate(base):
    kd2.insert(co[s], i)
kd2.balance()
for p in sorted(set(pv[gv == 4].tolist())):
    ids = np.where(pv == p)[0]
    m = np.array([copy(i, kd2, base) for i in ids]).mean(0)
    Wt[ids] = m / max(m.sum(), 1e-9)
    count[4] = count.get(4, 0) + 1
print('RULE pieces per garment', count)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
