"""m410 weight rules by Smart Topology shell ('piece' attribute; labels written as the 'garment' attribute):
0 skin      torso + vest + arms + hands P00, head P01, trousers P02, boots P04/P05: Meshy weights + shoulder fade
            (upper arm -> clavicle over 7 cm medially) + neck/head skin free of the shoulders (gob2).
1 head      cap P03, eyes P16/P17: rigid B_Head.
3 straps    belt + pouch strap P10, belt piece P11, buckle P15, mask P14: per-vertex copy of the skin under them, no arm
            share, smoothed.
4 kit       pouch P06, boot-lace knot P18: rigid on the mean of the skin weights under them, no arm share.
5 bands     wrist band P12 (right), bangles P13 (left): per-vertex copy of the arm/hand skin under them, smoothed.
7 guards    shoulder caps P07/P08: per-vertex copy of the skin under them (arm kept), smoothed.
8 sheath    the empty sheath P09 and its throat P19: B_Pelvis 0.75 + B_L_Thigh 0.25 (a pelvis-rigid sheath went 3.7 cm into
            the forward-swinging thigh in the run; author_dagger.py keys the sheathed dagger to its deformed vertices).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
SKIN = {0, 1, 2, 4, 5}
LABEL = {3: 1, 16: 1, 17: 1, 10: 3, 11: 3, 15: 3, 14: 3, 6: 4, 18: 4, 12: 5, 13: 5, 7: 7, 8: 7, 9: 8, 19: 8}
lab = {p: (0 if p in SKIN else LABEL.get(p, 4)) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per label', {g: sorted(p for p, x in lab.items() if x == g) for g in (0, 1, 3, 4, 5, 7, 8)})
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
# body skin only (no hands/forearms) as the copy reference for accessories
ref = np.where(np.isin(pv, [0, 1, 2]))[0]
kd = KDTree(len(ref))
for i, s in enumerate(ref):
    kd.insert(co[s], i)
kd.balance()


def copy(i, tree=None, rr=None):
    tree = tree or kd; rr = ref if rr is None else rr
    hits = tree.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[rr[h[1]] for h in hits]]).sum(0) / w.sum()


aref = np.where(pv == 0)[0]                                       # torso shell with the arms and hands: the bands' reference
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
    elif g == 7:
        new = np.array([copy(i) for i in ids])
    elif g == 8:
        new[:, gi['B_Pelvis']] = 0.75; new[:, gi['B_L_Thigh']] = 0.25
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
