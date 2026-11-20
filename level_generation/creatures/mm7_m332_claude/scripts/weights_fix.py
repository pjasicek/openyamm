"""m332 weight rules by Smart Topology shell ('piece' attribute; labels written as the 'garment' attribute):
0 skin      body/head/shoes P00, hands P02/P03, vest P01: Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm
            medially) + neck/head skin free of the shoulders (gob2); the vest's arm share capped at VEST_ARM.
1 head      eyes P28/P29: rigid B_Head.
3 hair      ponytail P04: per-vertex copy of the body skin under it without arm/clavicle share, mixed with B_Head by depth
            below its top (1 -> HEAD_LOW at the tip), smoothed.
4 kit       vest studs and lacing crosses: rigid on the mean of the vest/skin weights under them, no arm share.
5 band      right upper-arm band P09: per-vertex copy of the arm skin under it.
6 belt      belt P05, buckle P15, dagger and sheath P06/P07/P08/P23/P25/P31: rigid on B_Pelvis.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
SKIN = {0, 1, 2, 3}
LABEL = {28: 1, 29: 1, 4: 3, 9: 5, 5: 6, 15: 6, 6: 6, 7: 6, 8: 6, 23: 6, 25: 6, 31: 6}
VEST_ARM, HEAD_LOW = 0.3, 0.6
lab = {p: (0 if p in SKIN else LABEL.get(p, 4)) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per label', {g: sorted(p for p, x in lab.items() if x == g) for g in (0, 1, 3, 4, 5, 6)})
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
# the vest: arm share capped (its armhole trim stays on the torso)
ves = np.where(pv == 1)[0]
arm = Wt[np.ix_(ves, ARMS)].sum(1); k = np.where(arm > VEST_ARM, VEST_ARM / np.maximum(arm, 1e-9), 1.0)
rest = 1 - arm; Wt[np.ix_(ves, ARMS)] *= k[:, None]
non = [i for i in range(len(names)) if i not in ARMS]
Wt[np.ix_(ves, non)] *= ((1 - arm * k) / np.maximum(rest, 1e-9))[:, None]
print('RULE vest arm share capped at', VEST_ARM, ': vertices', int((arm > VEST_ARM).sum()))
# body skin only (no hands/forearms) as the copy reference for accessories
ref = np.where(np.isin(pv, [0, 1]) & (Wt[:, ARMS].sum(1) < 0.05))[0]   # torso/neck/face skin and the vest
aref = np.where((pv == 0) & (Wt[:, ARMS].sum(1) > 0.5))[0]                # arm skin (the band's copy)
akd = KDTree(len(aref))
for i_, s_ in enumerate(aref):
    akd.insert(co[s_], i_)
akd.balance()
kd = KDTree(len(ref))
for i, s in enumerate(ref):
    kd.insert(co[s], i)
kd.balance()


def copy(i, tree=None, rr=None):
    tree = tree or kd; rr = ref if rr is None else rr
    hits = tree.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[rr[h[1]] for h in hits]]).sum(0) / w.sum()


edges = np.array([tuple(e.vertices) for e in me.edges])
for p, g in lab.items():
    if g == 0:
        continue
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names)))
    if g == 1:
        new[:, gi['B_Head']] = 1
    elif g == 6:
        new[:, gi['B_Pelvis']] = 1
    elif g == 5:
        new = np.array([copy(i, akd, aref) for i in ids])
    elif g == 4:
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0
        C /= np.maximum(C.sum(1, keepdims=True), 1e-9); new = np.tile(C.mean(0), (len(ids), 1))
    else:
        C = np.array([copy(i) for i in ids]); C[:, ARMS + [gi[n] for n in names if 'Clavicle' in n]] = 0
        C /= np.maximum(C.sum(1, keepdims=True), 1e-9)
        z = co[ids][:, 2]; t = np.clip((z.max() - z) / max(z.max() - z.min(), 1e-3), 0, 1)
        h = (1 - t * (1 - HEAD_LOW))[:, None]
        new = C * (1 - h); new[:, gi['B_Head']] += h[:, 0]
    Wt[ids] = new
strap = np.isin(gv, [3])
E = edges[strap[edges[:, 0]] & strap[edges[:, 1]]]
for _ in range(3):
    acc = Wt.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    Wt[strap] = (acc / deg[:, None])[strap]
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
print('RULE arm share on beard/hair max', round(float(Wt[np.isin(gv, [3])][:, ARMS].sum(1).max()), 3))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
