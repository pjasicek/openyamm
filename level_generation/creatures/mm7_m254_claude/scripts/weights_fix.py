"""m254 golem weight rules by Smart Topology shell ('piece' attribute; labels written as the 'garment' attribute).
Run after build_rig.py's Meshy transfer and twist_bones.py (the cuffs take the twist bones' share rigidly).
0 skin     P00 (one closed cast-metal body: torso, head, arms, hands, legs, feet): Meshy weights + shoulder fade (upper
           arm -> clavicle over 7 cm medially) + neck/head skin free of the shoulders (gob2/m414 rules).
1 head     crown P03, beard P06, horns P07/P08, horn sockets P13/P14, eyes P15/P16, ear studs P41/P42: rigid B_Head.
2 nemes    headdress cloth P04: B_Head above the head joint, blending to B_Neck, then B_Spine2 by height (lappets on the
           collar, back flap on the shoulders), no arm weight.
3 belt     belt band P05: per-vertex copy of the skin under it, no arm share, smoothed.
4 collar   broad collar P02: per-vertex copy of the skin under it, smoothed; arm share capped at 0.35 (rest to the
           clavicle of that side), neck/head share moved to B_Spine2 (the plate does not follow the head).
5 studs    collar studs P17-P40: rigid on the mean of the nearest collar vertices' final weights.
6 loincloth P01: the waist wrap (z > 0.88) as the belt; the front apron and the back panel from the pelvis at the wrap
           to 80 % thighs at the hem, ONE left/right mixture for the narrow front apron (0.5) and a gentle one across the
           wide back panel (0.25..0.75 from its x).
7 cuffs    wrist cuffs P11/P12, ankle cuffs P09/P10: rigid on the mean skin weights under them.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
LABEL = {0: 0, 3: 1, 6: 1, 7: 1, 8: 1, 13: 1, 14: 1, 15: 1, 16: 1, 41: 1, 42: 1, 4: 2, 5: 3, 2: 4, 1: 6,
         9: 7, 10: 7, 11: 7, 12: 7}
lab = {p: LABEL.get(p, 5 if 17 <= p <= 40 else -1) for p in sorted(set(pv.tolist()))}
assert all(g >= 0 for g in lab.values()), lab
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per label', {g: sorted(p for p, x in lab.items() if x == g) for g in range(8)})
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


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


skin = np.where(gv == 0)[0]
moved = 0
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    m = (co[skin] - sh) @ d
    keep = np.clip(1.0 + m / 0.07, 0, 1)
    dw = Wt[skin, ua] * (1 - keep) * (m < 0)
    Wt[skin, ua] -= dw; Wt[skin, cv] += dw; moved += int((dw > 1e-3).sum())
print('RULE skin shoulder fade: vertices changed', moved)
jz = J('B_Head')[2] - 0.02; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm', 'UpperArmTwist'))]
fz = np.clip((co[skin, 2] - (jz - 0.03)) / 0.03, 0, 1)
r = fz * (1 - np.clip((np.abs(co[skin, 0] - ax_x) - 0.07) / 0.07, 0, 1))
dw = Wt[np.ix_(skin, SH)].sum(1) * r
Wt[np.ix_(skin, SH)] *= (1 - r)[:, None]
np.add.at(Wt, (skin, np.where(co[skin, 2] > jz, gi['B_Head'], gi['B_Neck'])), dw)
print('RULE skin neck/head free of the shoulders: vertices changed', int((dw > 1e-4).sum()))
kd = KDTree(len(skin))
for i, s_ in enumerate(skin):
    kd.insert(co[s_], i)
kd.balance()


def copy(i):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()


def no_arms(C):
    C = C.copy(); C[:, ARMS] = 0
    return C / np.maximum(C.sum(1, keepdims=True), 1e-9)


NEW = Wt.copy()
# 1 head rigid
ids = np.where(gv == 1)[0]; NEW[ids] = 0; NEW[ids, gi['B_Head']] = 1
# 2 nemes: head -> neck -> upper chest by height
ids = np.where(gv == 2)[0]; z = co[ids, 2]
zH, zN, zS2 = J('B_Head')[2], J('B_Neck')[2], J('B_Spine2')[2]
th = ss((z - zN) / max(zH - zN, 1e-3)); tn = ss((z - zS2) / max(zN - zS2, 1e-3))
W = np.zeros((len(ids), len(names)))
W[:, gi['B_Head']] = th; W[:, gi['B_Neck']] = (1 - th) * tn; W[:, gi['B_Spine2']] = (1 - th) * (1 - tn)
NEW[ids] = W
# 3 belt
ids = np.where(gv == 3)[0]; NEW[ids] = no_arms(np.array([copy(i) for i in ids]))
# 4 collar
ids = np.where(gv == 4)[0]; C = np.array([copy(i) for i in ids])
for s in ('L', 'R'):
    side = idx((f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'B_{s}_Finger'))
    arm = C[:, side].sum(1); over = np.maximum(arm - 0.35, 0)
    C[:, side] *= np.where(arm > 1e-6, (arm - over) / np.maximum(arm, 1e-9), 1)[:, None]
    C[:, gi[f'B_{s}_Clavicle']] += over
for n in ('B_Neck', 'B_Head'):
    C[:, gi['B_Spine2']] += C[:, gi[n]]; C[:, gi[n]] = 0
NEW[ids] = C
# 6 loincloth
ids = np.where(gv == 6)[0]; z = co[ids, 2]; x = co[ids, 0]
belt = no_arms(np.array([copy(i) for i in ids]))
TOP = 0.90; bot = z.min()
a_ = 0.8 * np.clip((TOP - z) / max(TOP - bot, 1e-3), 0, 1)
y_mid = J('B_Pelvis')[1]
front = co[ids, 1] < y_mid
wl = np.where(front, 0.5, 0.5 + 0.5 * np.clip(x / 0.36, -1, 1))
S = np.zeros((len(ids), len(names)))
S[:, gi['B_Pelvis']] = 1 - a_; S[:, gi['B_L_Thigh']] = a_ * wl; S[:, gi['B_R_Thigh']] = a_ * (1 - wl)
wb = ss((z - 0.86) / 0.05)[:, None]
NEW[ids] = wb * belt + (1 - wb) * S
# 7 cuffs: rigid on the mean of the skin under them
for p in [p for p, g in lab.items() if g == 7]:
    ids = np.where(pv == p)[0]; C = np.array([copy(i) for i in ids]).mean(0)
    NEW[ids] = C / C.sum()
# smoothing over the belt, collar and loincloth edges
edges = np.array([tuple(e.vertices) for e in me.edges])
strap = np.isin(gv, [3, 4, 6])
E = edges[strap[edges[:, 0]] & strap[edges[:, 1]]]
for _ in range(3):
    acc = NEW.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], NEW[E[:, 1]]); np.add.at(acc, E[:, 1], NEW[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    NEW[strap] = (acc / deg[:, None])[strap]
# 5 studs: rigid on the mean of the nearest collar vertices (after the collar's smoothing)
col = np.where(gv == 4)[0]
ck = KDTree(len(col))
for i, s_ in enumerate(col):
    ck.insert(co[s_], i)
ck.balance()
for p in [p for p, g in lab.items() if g == 5]:
    ids = np.where(pv == p)[0]; acc = np.zeros(len(names))
    for i in ids:
        for c_, j, d_ in ck.find_n(co[i], 6):
            acc += NEW[col[j]]
    NEW[ids] = acc / acc.sum()
NEW /= np.maximum(NEW.sum(1, keepdims=True), 1e-9)
print('RULE arm share max: collar', round(float(NEW[gv == 4][:, ARMS].sum(1).max()), 3), 'nemes',
      round(float(NEW[gv == 2][:, ARMS].sum(1).max()), 3), 'loincloth', round(float(NEW[gv == 6][:, ARMS].sum(1).max()), 3),
      'belt', round(float(NEW[gv == 3][:, ARMS].sum(1).max()), 3))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(NEW[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(NEW[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
