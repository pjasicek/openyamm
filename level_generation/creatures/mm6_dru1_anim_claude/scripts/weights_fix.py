"""G4 weight rules (druidess version: per-piece rules in the DRUIDESS block; goblin history below) (measured faults: armlets 9x, chest armour 6.6x, shoulder skin 5x stretch in the attack).
1. Every shell except the skin (piece 0) and the hair (1) copies the weights of the nearest skin vertices (inverse
   distance over the 4 nearest), so armour follows the body under it instead of Meshy's own guesses.
2. Torso armour (shell centroid within the ribcage box) drops upper-arm/forearm/hand weight, renormalised.
3. (dropped) small limb rings rigid on their dominant bone - see the note in the loop.
4. Skin: upper-arm weight fades out medially across the shoulder - full at the shoulder joint, zero 7 cm toward the
   midline (measured along the clavicle direction) - and the removed weight goes to the clavicle.
Each rule reports what it changed. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
tris = {p: 0 for p in np.unique(pv)}
for poly in me.polygons:
    tris[int(pv[poly.vertices[0]])] += len(poly.vertices) - 2
ARM = [gi[n] for n in names if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]   # incl. twist bones
# DRUIDESS pieces (step1_clean.py): 0 skin (torso, upper arms, neck, face), 2 legs, 4/5 hands, 6/7 boots, 9/10 bracers
# (they ARE the forearms) - all body SURFACE, they keep Meshy's weights (hands get fingers at G5; the twist ramp
# moves the bracers onto the twist bones). 100 the cloak (cloak_rig.py replaces every cloak weight). 8 belt and
# 14 medallion: skin copy without arm weight. 11 front panel of the bodysuit: pelvis at the belt -> both thighs at the
# tip (one 50/50 mixture, the goblin skirt-strip rule). 3 hood and 1 hair: Head above the head joint, ramping to the
# neck and upper chest below it (the hood rests on the shoulders, the hair hangs over the chest).
SURFACE = (0, 2, 4, 5, 6, 7, 9, 10)
skin = np.where(np.isin(pv, (0, 2)))[0]
kd = KDTree(len(skin))
for i, s_ in enumerate(skin):
    kd.insert(co[s_], i)
kd.balance()
J = lambda n: np.array(rig.data.bones[n].head_local)
PEL = gi['B_Pelvis']


def skin_copy(ids):
    new = np.zeros((len(ids), len(names)))
    for k, i in enumerate(ids):
        hits = kd.find_n(co[i], 4)
        w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        new[k] = (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    return new


for p in (8, 14):                                          # review 3: rigid (skin copies twisted the belt per stride)
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names))); new[:, PEL] = 0.7; new[:, gi['B_Spine']] = 0.3
    Wt[ids] = new
    print('RULE piece', p, tris[p], 'tris: rigid belt (pelvis 0.7, spine 0.3)')
ids = np.where(pv == 11)[0]
z = co[ids][:, 2]; top, bot = z.max(), z.min()
a = np.clip((top - z) / max(top - bot, 1e-3), 0, 1)
new = np.zeros((len(ids), len(names))); new[:, PEL] = 1 - a
new[:, gi['B_L_Thigh']] = a * 0.5; new[:, gi['B_R_Thigh']] = a * 0.5
Wt[ids] = new
print('RULE piece 11', tris[11], 'tris: front panel pelvis -> thighs 50/50 at the tip')
zh, zn, zc = J('B_Head')[2], J('B_Neck')[2], J('B_Spine2')[2]
for p in (1, 3):
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names)))
    for k, i in enumerate(ids):
        zz = co[i, 2]
        h = float(np.clip((zz - zn) / max(zh - zn, 1e-3), 0, 1))         # 1 at/above the head joint
        n_ = float(np.clip((zz - zc) / max(zn - zc, 1e-3), 0, 1)) * (1 - h)  # neck between the chest and the head
        new[k, gi['B_Head']] = h; new[k, gi['B_Neck']] = n_; new[k, gi['B_Spine2']] = max(0.0, 1 - h - n_)
    Wt[ids] = new
    print('RULE piece', p, tris[p], 'tris: head -> neck -> upper chest by height')
for p in (6, 7):
    ids = np.where(pv == p)[0]
    LEG = [gi[n] for n in names if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
    keep = np.zeros(len(names)); keep[LEG] = 1
    new = Wt[ids] * keep
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    print('RULE piece', p, tris[p], 'tris: boot keeps only leg weights')
# 6. limbs do not share weight across the hip (G4, druidess): in the A-pose the hands hang beside the hips, and Meshy gave
#    the bracers/forearm skin up to 27 % thigh weight (12-43x stretch when she kneels or casts) - the thief had the
#    reverse (hand weight on a knee). Arm vertices (hands, bracers, and skin with >= 50 % arm weight of one side) lose
#    all leg and pelvis weight; leg vertices (legs, boots, front panel, skin with >= 50 % leg weight) lose all arm weight.
LEGW = [gi[n] for n in names if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))] + [gi['B_Pelvis']]
ARMW = ARM + [gi[n] for n in names if 'Clavicle' in n]
armv = np.isin(pv, (4, 5, 9, 10)) | ((pv == 0) & (Wt[:, ARMW].sum(1) >= 0.5))
legv = np.isin(pv, (2, 6, 7, 11)) | ((pv == 0) & (Wt[:, LEGW].sum(1) >= 0.5))
ca = int((Wt[armv][:, LEGW].sum(1) > 1e-3).sum()); cl_ = int((Wt[legv][:, ARMW].sum(1) > 1e-3).sum())
Wt[np.ix_(armv, LEGW)] = 0; Wt[np.ix_(legv, ARMW)] = 0
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
print('RULE limbs apart: arm vertices that lost leg/pelvis weight', ca, '; leg vertices that lost arm weight', cl_)
# 8. no head weight on the shoulders (G4, druidess): Meshy gave the shoulder-top skin at the shoulder joints 36-49 %
#    B_Head (the hood rests there), so the shoulder tops followed the head (3.2x in the death). Skin lateral of the neck
#    loses its head weight over |x - neck x| 0.06 -> 0.09 m, into B_Spine2.
nx = J('B_Neck')[0]; moved8 = 0
for i in np.where(pv == 0)[0]:
    f8 = float(np.clip((abs(co[i, 0] - nx) - 0.06) / 0.03, 0, 1))
    h8 = Wt[i, gi['B_Head']] * f8
    if h8 > 1e-4:
        Wt[i, gi['B_Head']] -= h8; Wt[i, gi['B_Spine2']] += h8; moved8 += 1
print('RULE no head weight on the shoulders: skin vertices changed', moved8)
# 7. armpit transition (G4, druidess): Meshy's lats/side-chest skin carries 88-96 % upper-arm weight up to a narrow
#    seam, so the raised attack arm stretched it 3.6x and the arm behind the body in the death 4.1x. Stripping that
#    arm weight (two tries: a fixed arm radius, then a spine/arm distance ratio) made the seam harder (6-10x). Instead
#    the weights are diffused over the skin's own edges in the armpit region (skin within ARMPIT_R of the point below
#    the shoulder joint), ARMPIT_PASSES passes, which widens the transition from arm to torso.
ARMPIT_R, ARMPIT_PASSES = float(os.environ.get('ARMPIT_R', '0.12')), int(os.environ.get('ARMPIT_PASSES', '8'))
nbr7 = [[] for _ in range(nv)]
for e in me.edges:
    a_, b_ = e.vertices
    if pv[a_] == 0 and pv[b_] == 0:
        nbr7[a_].append(b_); nbr7[b_].append(a_)
region = np.zeros(nv, bool)
for s_ in ('L', 'R'):
    ap = J(f'B_{s_}_UpperArm') + np.array([-np.sign(J(f'B_{s_}_UpperArm')[0]) * 0.03, 0.0, -0.08])   # armpit point
    region |= (pv == 0) & (np.linalg.norm(co - ap, axis=1) < ARMPIT_R)
idx7 = np.where(region)[0]
for _ in range(ARMPIT_PASSES):
    nxt = Wt.copy()
    for i in idx7:
        if nbr7[i]:
            nxt[i] = 0.5 * Wt[i] + 0.5 * Wt[nbr7[i]].mean(0)
    Wt = nxt
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
print('RULE armpit diffusion: skin vertices', len(idx7), 'passes', ARMPIT_PASSES, 'radius', ARMPIT_R)
# 4. shoulder fade on the skin
moved = 0
skin = np.where(pv == 0)[0]
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)                       # clavicle direction, pointing out to the shoulder
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    for i in skin:
        m = (co[i] - sh) @ d                                        # > 0 outside the joint, < 0 toward the midline
        if m < 0 and Wt[i, ua] > 0:
            keep = max(0.0, 1.0 + m / 0.07)
            dw = Wt[i, ua] * (1 - keep)
            Wt[i, ua] -= dw; Wt[i, cv] += dw; moved += dw > 1e-3
print('RULE shoulder fade: skin vertices changed', moved)
# 5. jaw free of the shoulders (gob2 review 2): Meshy weighted even the jaw underside 21-37 % to the clavicles/upper
#    arms, so a shrug dragged the jaw down onto the shoulder. Skin above the jaw line (B_Head joint - 2 cm, ramp over
#    3 cm below it) inside the neck's width loses that weight to the neck/head; the side of the neck below keeps it and
#    still lifts with a shrug (a first version cleaned the whole neck above the clavicles: the jaw then stayed put and
#    the shoulder met it 5 cm deep instead of 2 cm).
jz = J('B_Head')[2] - 0.02; nz = J('B_Neck')[2]; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm', 'UpperArmTwist'))]
neck_moved = 0
for i in skin:
    fz = float(np.clip((co[i, 2] - (jz - 0.03)) / 0.03, 0, 1))
    if fz <= 0:
        continue
    keep_lat = float(np.clip((abs(co[i, 0] - ax_x) - 0.07) / 0.07, 0, 1))
    r = fz * (1 - keep_lat)
    dw = Wt[i, SH].sum() * r
    if dw > 1e-4:
        Wt[i, SH] *= (1 - r)
        Wt[i, gi['B_Head'] if co[i, 2] > jz else gi['B_Neck']] += dw; neck_moved += 1
print('RULE jaw free of the shoulders: skin vertices changed', neck_moved)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
