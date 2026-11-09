"""m438 weight rules by Smart Topology shell ('piece' attribute; labels written as the 'garment' attribute):
0 skin      P00 head/torso/arms (right arm a stump), feet P02/P03, the rebuilt right shin P16: Meshy weights + shoulder
            fade (upper arm -> clavicle over 7 cm medially) + neck/head skin free of the shoulders (gob2). The stump
            has no hand: Meshy's right-hand share (its "hand" sat on the stump end) moves to B_R_Forearm, so the
            unweighted right hand/finger bones cannot bend the stump.
1 head      teeth P13, eyes P14/P15: rigid B_Head.
2 trousers  P01: Meshy weights with every arm share removed (the left hand hangs beside the thigh), smoothed.
3 rope      belt P04 and its hanging ends P05: per-vertex copy of the trousers/skin under them, no arm share, smoothed.
4 stump     bone tips P06-P09: rigid B_R_Forearm.
5 shin bone rods P10-P12: per-vertex copy of the shin/foot skin under them (they run from the knee into the foot).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
SKIN = {0, 2, 3, 16}
LABEL = {13: 1, 14: 1, 15: 1, 1: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}
lab = {p: (0 if p in SKIN else LABEL[p]) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per label', {g: sorted(p for p, x in lab.items() if x == g) for g in range(6)})
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
# stump: the right hand and finger share -> the forearm (twist bones keep theirs)
RH = [gi[n] for n in names if n.startswith('B_R_') and ('Hand' in n or 'Finger' in n)]
st = Wt[:, RH].sum(1)
Wt[:, gi['B_R_Forearm']] += st; Wt[:, RH] = 0
print('RULE stump: right hand/finger share moved to the forearm on', int((st > 1e-4).sum()), 'vertices, max', round(float(st.max()), 3))
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


def tree(pieces):
    rr = np.where(np.isin(pv, pieces))[0]
    kd = KDTree(len(rr))
    for i, s_ in enumerate(rr):
        kd.insert(co[s_], i)
    kd.balance()
    return kd, rr


def copy(i, kd, rr):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[rr[h[1]] for h in hits]]).sum(0) / w.sum()


# trousers: no arm share
tr = gv == 2
arm_tr = Wt[tr][:, ARMS].sum(1)
Wt[np.ix_(tr, ARMS)] = 0
print('RULE trousers arm share removed: vertices', int((arm_tr > 1e-4).sum()), 'max', round(float(arm_tr.max()), 3))
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
kd_t, rr_t = tree([1, 0])                                       # trousers + torso skin under the belt
kd_s, rr_s = tree([16, 2])                                      # the shin and the right foot
for p, g in lab.items():
    if g in (0, 2):
        continue
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names)))
    if g == 1:
        new[:, gi['B_Head']] = 1
    elif g == 3:
        new = np.array([copy(i, kd_t, rr_t) for i in ids]); new[:, ARMS] = 0
    elif g == 4:
        new[:, gi['B_R_Forearm']] = 1
    elif g == 5:
        new = np.array([copy(i, kd_s, rr_s) for i in ids])
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
edges = np.array([tuple(e.vertices) for e in me.edges])
for labels, passes in (([2], 2), ([3], 3), ([5], 2)):
    m = np.isin(gv, labels)
    E = edges[m[edges[:, 0]] & m[edges[:, 1]]]
    for _ in range(passes):
        acc = Wt.copy(); deg = np.ones(nv)
        np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
        np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
        Wt[m] = (acc / deg[:, None])[m]
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
print('RULE arm share on trousers/rope max', round(float(Wt[np.isin(gv, [2, 3])][:, ARMS].sum(1).max()), 3),
      '| right hand/finger share max', round(float(Wt[:, RH].sum(1).max()), 4))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
