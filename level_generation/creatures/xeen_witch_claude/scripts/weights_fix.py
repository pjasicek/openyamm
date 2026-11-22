"""Witch weight rules, by garment (scripts/garments.py 'garment' attribute):
0 body       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw free of the shoulders (gob2);
             the robe skirt (P00 below the hips) keeps Meshy's leg weights but no arm weight (A-pose hands hang beside it).
1 hair       the mane: rigid head above the neck joint, blending toward the chest (B_Spine2) for strands that hang lower
             (t = (z_neck - z) / 0.25, capped 0.7), so the mane follows the head without shearing at the shoulders.
2 mask       horned crown, jaw/collar piece and forehead gem: rigid head.
3 panel      black front apron and its bands: pelvis at the top -> an even left/right thigh mixture (max 0.55) at the hem
             (one mixture for the whole centred panel, bands take the panel's function of height).
4 beads      rigid per piece on the skin weights nearest the bead, no arm weight.
5 studs      rigid on the bone that dominates the skin under them (wrist wrap / gauntlet).
6 spikes     rigid on the bone that dominates the boot under them.
7 tatters    per-vertex copy of the skin under them (4 nearest, inverse distance).
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
# robe skirt: no arm weight below the hips (the hanging A-pose hands sat beside it in Meshy's solve)
pz = J('B_Pelvis')[2]
sk_low = skin[(co[skin, 2] < pz - 0.05) & (pv[skin] == 0)]
a_ = Wt[np.ix_(sk_low, ARMS)].sum(1)
Wt[np.ix_(sk_low, ARMS)] = 0; Wt[sk_low, PEL] += a_
# forearm / hand / finger weight belongs on the arm and hand shells only (P08/P09 arms, P02/P03 hands): Meshy gave
# torso and robe vertices near the A-pose hands some (G6 found them 4-6 cm inside the hips in the casts)
LOW = [gi[n] for n in names if any(k in n for k in ('Forearm', '_Hand', 'Finger'))]
off = skin[~np.isin(pv[skin], (2, 3, 8, 9))]
lw = Wt[np.ix_(off, LOW)].sum(1)
Wt[np.ix_(off, LOW)] = 0
empty = Wt[off].sum(1) < 1e-6
Wt[off[empty], gi['B_Spine']] = 1
print('RULE forearm/hand weight off the torso and robe: vertices', int((lw > 1e-3).sum()), 'max', round(float(lw.max()) if len(lw) else 0, 3))
print('RULE robe skirt arm weight removed: vertices', int((a_ > 1e-3).sum()), 'max', round(float(a_.max()) if len(a_) else 0, 3))
Wt[skin] /= np.maximum(Wt[skin].sum(1, keepdims=True), 1e-9)
kd = KDTree(len(skin))
for i, s_ in enumerate(skin):
    kd.insert(co[s_], i)
kd.balance()
edges = np.array([tuple(e.vertices) for e in me.edges])
count = {}
zn = J('B_Neck')[2]; HEAD, CHEST = gi['B_Head'], gi['B_Spine2']
pzl = co[pv == 10][:, 2]; ptop, pbot = float(pzl.max()), float(pzl.min())
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    new = np.zeros((len(ids), len(names)))
    if g == 1:
        t = np.clip((zn - co[ids, 2]) / 0.25, 0, 0.7)
        new[:, HEAD] = 1 - t; new[:, CHEST] = t
    elif g == 2:
        new[:, HEAD] = 1
    elif g == 3:
        a = np.clip((ptop - 0.06 - co[ids, 2]) / max(ptop - 0.06 - pbot, 1e-3), 0, 1) * 0.55
        new[:, PEL] = 1 - a; new[:, gi['B_L_Thigh']] = a / 2; new[:, gi['B_R_Thigh']] = a / 2
    elif g == 4:
        m = copy(ids[np.argmax(co[ids, 2])]); m[ARMS] = 0; new[:] = norm(m)
    elif g in (5, 6):
        m = np.array([copy(i) for i in ids]).mean(0); dom = int(np.argmax(m)); new[:, dom] = 1
        print('RULE rigid piece', p, 'garment', g, 'on', names[dom], 'skin share', round(float(m[dom]), 2))
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
