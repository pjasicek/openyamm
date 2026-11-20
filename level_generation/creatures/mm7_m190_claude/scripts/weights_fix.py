"""m190 weight rules by Smart Topology shell ('piece' attribute; labels written as the 'garment' attribute):
0 skin      torso/head/beard/hair/collar P00, boots P01/P02, legs P06, hands P04/P05, bare upper arms P15/P16: Meshy
            weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + neck/head skin free of the shoulders
            (gob2) + the beard free of the arms and clavicles (front of the chest, |x| < 13 cm).
1 head      helmet P08, horns P17/P18, eyes P24/P25: rigid B_Head.
3 braids    P09/P10 and the braid ends P21/P22: per-vertex copy of the skin (beard) under them, no arm share, smoothed.
4 kit       buckle P23: rigid on the mean of the skin weights under it, no arm share.
5 bracers   P11 (left), P12 (right): per-vertex copy of the arm skin and hand under them (the rim follows the wrist:
            rigid bracers opened a gap at the hand shell when the wrist bent), smoothed.
6 skirts    ragged green skirt P03 and mail skirt P07: pelvis at the top -> the thighs at the hem, the left/right mixture per
            vertex from its x (a skirt around the body, unlike natm's per-side panels); blended into a copy of the skin under it where
            it lies on the body (within 1.5 cm full copy, rule from 5 cm), so the hip skin cannot poke through.
7 guards    shoulder guards P13/P14 and rims P19/P20: per-vertex copy of the skin under them (arm kept), smoothed.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
SKIN = {0, 1, 2, 4, 5, 6, 15, 16}
LABEL = {8: 1, 17: 1, 18: 1, 24: 1, 25: 1, 9: 3, 10: 3, 21: 3, 22: 3, 23: 4, 11: 5, 12: 5, 3: 6, 7: 6,
         13: 7, 14: 7, 19: 7, 20: 7}
lab = {p: (0 if p in SKIN else LABEL.get(p, 4)) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per label', {g: sorted(p for p, x in lab.items() if x == g) for g in (0, 1, 3, 4, 5, 6, 7)})
json.dump({str(p): g for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
J = lambda n: np.array(rig.data.bones[n].head_local)
idx = lambda keys: [gi[n] for n in names if any(k in n for k in keys)]
ARMS = idx(('UpperArm', 'Forearm', 'Hand', 'Finger'))
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
print('RULE skin neck/head free of the shoulders: vertices changed', neck_moved)
# the beard hangs in front of the chest inside the torso shell: no arm or clavicle weight on it
ARMCL = ARMS + [gi[n] for n in names if 'Clavicle' in n]
front = np.percentile(co[(pv == 0) & (np.abs(co[:, 0]) < 0.05) & (co[:, 2] > 0.75) & (co[:, 2] < 0.9)][:, 1], 5)
beard = (pv == 0) & (np.abs(co[:, 0]) < 0.13) & (co[:, 2] > 0.66) & (co[:, 2] < J('B_Head')[2]) & (co[:, 1] < front + 0.06)
dw = Wt[beard][:, ARMCL].sum(1)
Wt[np.ix_(beard, ARMCL)] = 0
print('RULE beard free of the arms/clavicles: vertices', int(beard.sum()), 'arm share removed max', round(float(dw.max()) if len(dw) else 0, 3))
# body skin only (no hands/forearms) as the copy reference for accessories
ref = np.where(np.isin(pv, [0, 6, 15, 16]))[0]
kd = KDTree(len(ref))
for i, s in enumerate(ref):
    kd.insert(co[s], i)
kd.balance()


def copy(i, tree=None, rr=None):
    tree = tree or kd; rr = ref if rr is None else rr
    hits = tree.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[rr[h[1]] for h in hits]]).sum(0) / w.sum()


aref = np.where(np.isin(pv, [15, 16, 4, 5]))[0]                 # arm skin + hands: the bracers' copy reference
akd = KDTree(len(aref))
for i, s_ in enumerate(aref):
    akd.insert(co[s_], i)
akd.balance()


edges = np.array([tuple(e.vertices) for e in me.edges])
for p, g in lab.items():
    if g == 0:
        continue
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names)))
    if g == 1:
        new[:, gi['B_Head']] = 1
    elif g == 5:
        new = np.array([copy(i, akd, aref) for i in ids])
    elif g == 6:
        PEL = gi['B_Pelvis']; z = co[ids][:, 2]
        top, bot = z.max(), z.min()
        a_ = np.clip((top - z) / max(top - bot, 1e-3), 0, 1)
        wl = np.clip(0.5 + co[ids][:, 0] / 0.12, 0, 1)
        new[:, PEL] = 1 - a_; new[:, gi['B_L_Thigh']] = a_ * wl; new[:, gi['B_R_Thigh']] = a_ * (1 - wl)
        # where the skirt lies on the skin it takes the skin's weights (user review 2026-10-20: the hip and thigh skin
        # follows the thigh more than the pelvis-heavy skirt top and poked through the mail in the walk): full copy
        # within SKIRT_GAP[0] of the body skin, the rule from SKIRT_GAP[1] on
        g0, g1 = (float(x) for x in os.environ.get('SKIRT_GAP', '0.015,0.05').split(','))
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0; C /= np.maximum(C.sum(1, keepdims=True), 1e-9)
        gap = np.array([kd.find(co[i])[2] for i in ids])
        k = np.clip((g1 - gap) / (g1 - g0), 0, 1)[:, None]
        new = k * C + (1 - k) * new
        print(f'RULE skirt P{p:02d}: skin copy share mean {float(k.mean()):.2f}, full on {int((k >= 1).sum())} of {len(ids)}')
    elif g == 7:
        new = np.array([copy(i) for i in ids])
    else:
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0
        C /= np.maximum(C.sum(1, keepdims=True), 1e-9)
        new = C if g == 3 else np.tile(C.mean(0), (len(ids), 1))
    Wt[ids] = new
strap = np.isin(gv, [3, 5, 7])
E = edges[strap[edges[:, 0]] & strap[edges[:, 1]]]
for _ in range(3):
    acc = Wt.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    Wt[strap] = (acc / deg[:, None])[strap]
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
print('RULE arm share on braids/kit/skirts max', round(float(Wt[np.isin(gv, [3, 4, 6])][:, ARMS].sum(1).max()), 3))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
