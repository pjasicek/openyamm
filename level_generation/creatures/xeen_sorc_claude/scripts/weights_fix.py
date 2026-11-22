"""Sorceress weight rules, by garment (scripts/garments.py 'garment' attribute):
0 body       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw free of the shoulders (gob2);
             no arm weight on the torso/hips/thighs (inside |x| < 0.26 m, 10 cm below the shoulders and over 8.5 cm from the arm's
             joint polyline: the A-pose hands hang 25 cm
             out, but Meshy's solve leaks some forearm/hand weight onto the hips).
1 hair       the mane: rigid head above the neck joint, blending toward the chest (B_Spine2) for curls that hang lower
             (t = (z_neck - z) / 0.25, capped 0.7), so the mane follows the head without shearing at the shoulders.
2 head       eyes, lips, circlet and earrings: rigid head.
3/7 panels   front (3) and back (7) cloth panels: pelvis at the girdle, ramping over 8 cm onto B_PanelFront /
             B_PanelBack (panel_bones.py: they swing with the more flexed / extended thigh).
4 caps       shoulder caps and their studs: per-vertex copy of the skin under them, with the upper-arm share capped at
             0.5 (the rest to the clavicle) so a raised arm does not tear them off the shoulder.
5 jewellery  choker and chest pieces: rigid per piece on the skin weights nearest its top vertex, no arm weight.
6 girdle     girdle, gems and studs: per-vertex copy of the skin under them without arm weight, legs capped at 0.35
             (the rest to the pelvis) so the hard band does not fold with the thighs.
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
LEG = {s: idx((f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe')) for s in 'LR'}
LEGS = LEG['L'] + LEG['R']
PEL = gi['B_Pelvis']
skin = np.where(gv == 0)[0]
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()


def copy(i):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()


def norm(w):
    return w / max(w.sum(), 1e-9)


# skin rules first (the accessories copy the final skin) ------------------------------------------------------------
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
# torso, hips and thighs carry no arm weight: the one skin shell holds the arms too, so the trunk is selected by
# position (inside |x| < 0.26 m and below the armpits; the A-pose hands hang ~0.43 m out)
pz = J('B_Pelvis')[2]; az = min(J('B_L_UpperArm')[2], J('B_R_UpperArm')[2]) - 0.10
def seg_dist(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, d)), axis=1)
armd = np.full(len(skin), 9.0)
for s_ in 'LR':
    sh_, el_, wr_ = J(f'B_{s_}_UpperArm'), J(f'B_{s_}_Forearm'), J(f'B_{s_}_Hand')
    tip_ = wr_ + (wr_ - el_) / np.linalg.norm(wr_ - el_) * 0.21
    for a0, b0 in ((sh_, el_), (el_, wr_), (wr_, tip_)):
        armd = np.minimum(armd, seg_dist(co[skin], a0, b0))
trunk = skin[(np.abs(co[skin, 0]) < 0.26) & (co[skin, 2] < az) & (armd > 0.085)]
a_ = Wt[np.ix_(trunk, ARMS)].sum(1)
Wt[np.ix_(trunk, ARMS)] = 0
spine = np.where(co[trunk, 2] < pz, PEL, gi['B_Spine'])
Wt[trunk, spine] += a_
print('RULE trunk arm weight removed: vertices', int((a_ > 1e-3).sum()), 'max', round(float(a_.max()) if len(a_) else 0, 3))
Wt[skin] /= np.maximum(Wt[skin].sum(1, keepdims=True), 1e-9)
kd = KDTree(len(skin))
for i, s_ in enumerate(skin):
    kd.insert(co[s_], i)
kd.balance()
edges = np.array([tuple(e.vertices) for e in me.edges])
count = {}
zn = J('B_Neck')[2]; HEAD, CHEST = gi['B_Head'], gi['B_Spine2']
PANEL = {3: 4, 7: 6}                                            # garment -> piece
PZ = {g: (float(co[pv == p][:, 2].max()), float(co[pv == p][:, 2].min())) for g, p in PANEL.items()}
CL = {s: gi[f'B_{s}_Clavicle'] for s in 'LR'}; UA = {s: gi[f'B_{s}_UpperArm'] for s in 'LR'}
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    new = np.zeros((len(ids), len(names)))
    if g == 1:
        t = np.clip((zn - co[ids, 2]) / 0.25, 0, 0.7)
        new[:, HEAD] = 1 - t; new[:, CHEST] = t
    elif g == 2:
        new[:, HEAD] = 1
    elif g in (3, 7):
        ptop, pbot = PZ[g]
        pb_ = gi.get('B_PanelFront' if g == 3 else 'B_PanelBack')
        if pb_ is not None:                     # panel_bones.py: pelvis at the girdle, the panel bone from 5 cm below
            a = np.clip((ptop - 0.05 - co[ids, 2]) / 0.08, 0, 1)
            new[:, PEL] = 1 - a; new[:, pb_] = a
        else:
            a = np.clip((ptop - 0.06 - co[ids, 2]) / max(ptop - 0.06 - pbot, 1e-3), 0, 1) * 0.55
            new[:, PEL] = 1 - a; new[:, gi['B_L_Thigh']] = a / 2; new[:, gi['B_R_Thigh']] = a / 2
    elif g == 4:
        new = np.array([copy(i) for i in ids])
        for s_ in 'LR':
            ex = np.maximum(new[:, UA[s_]] - 0.5 * new.sum(1), 0)
            new[:, UA[s_]] -= ex; new[:, CL[s_]] += ex
    elif g == 5:
        m = copy(ids[np.argmax(co[ids, 2])]); m[ARMS] = 0; new[:] = norm(m)
    elif g == 6:
        new = np.array([copy(i) for i in ids]); new[:, ARMS] = 0
        new = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
        lg = new[:, LEGS].sum(1); k = np.where(lg > 0.35, 0.35 / np.maximum(lg, 1e-9), 1.0)
        moved_ = lg * (1 - k); new[:, LEGS] *= k[:, None]; new[:, PEL] += moved_
    else:
        new = np.array([copy(i) for i in ids])
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
