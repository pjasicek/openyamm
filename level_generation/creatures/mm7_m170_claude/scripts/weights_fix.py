"""natm weight rules, by garment (scripts/garments.py 'garment' attribute):
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw free of the shoulders (gob2).
1 mantle     per-vertex copy of the skin under it (4 nearest, inverse distance), legs moved to the pelvis (the cape
             hangs 10-20 cm behind the buttocks and must not follow the thighs), arm share capped at 0.25 (excess to
             the clavicle: shoulder feathers lift a little with a raised arm, they do not fly with it), then smoothed
             3 passes inside each card so no card tears.
2 hip trim   each card rigid on the MEAN of the skin weights under it, restricted to pelvis/spine/thighs.
3/4 guards   each card rigid on the mean skin weights under it, restricted to the leg it is on.
5/6 panels   loincloth strips: pelvis at the belt -> the thighs at the hem (one left/right mixture); belt rigid pelvis.
7 rings      rigid on the bone that dominates the skin under them.
8 beads      rigid per piece on the skin weights nearest the piece's top (where it hangs from), no arm weight.
9 eyes       rigid head.
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
# rebuild the skin reference after the skin edits
edges = np.array([tuple(e.vertices) for e in me.edges])
# accessories --------------------------------------------------------------------------------------------------------
count = {}
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    C = np.array([copy(i) for i in ids])
    if g == 1:
        for s in 'LR':
            # legs -> pelvis
            C[:, PEL] += C[:, LEG[s]].sum(1); C[:, LEG[s]] = 0
        for s in 'LR':
            a = C[:, ARM[s]].sum(1)
            over = np.clip(a - 0.25, 0, None)
            sc = np.where(a > 1e-9, (a - over) / np.maximum(a, 1e-9), 1)
            C[:, ARM[s]] *= sc[:, None]; C[:, gi[f'B_{s}_Clavicle']] += over
        new = C
    elif g == 2:
        m = C.mean(0); keep = np.zeros_like(m)
        for n in ('B_Pelvis', 'B_Spine', 'B_L_Thigh', 'B_R_Thigh'):
            keep[gi[n]] = m[gi[n]]
        new = np.tile(norm(keep), (len(ids), 1))
    elif g in (3, 4):
        s = 'L' if g == 3 else 'R'
        m = C.mean(0); keep = np.zeros_like(m); keep[LEG[s]] = m[LEG[s]]
        new = np.tile(norm(keep), (len(ids), 1))
    elif g in (5, 6):
        z = co[ids][:, 2]
        belt = z > (0.975 if g == 5 else z.max() - 0.02)
        top, bot = (z[~belt].max() if (~belt).any() else z.max()), z.min()
        a = np.clip((top - z) / max(top - bot, 1e-3), 0, 1)
        xc = float(co[ids][~belt][:, 0].mean()) if (~belt).any() else 0.0
        wl = float(np.clip(0.5 + xc / 0.12, 0, 1))
        new = np.zeros_like(C); new[:, PEL] = 1 - a
        new[:, gi['B_L_Thigh']] = a * wl; new[:, gi['B_R_Thigh']] = a * (1 - wl)
        new[belt] = 0; new[belt, PEL] = 1
    elif g == 7:
        m = C.mean(0); dom = int(np.argmax(m)); new = np.zeros_like(C); new[:, dom] = 1
        print('RULE ring piece', p, 'rigid on', names[dom], 'skin share', round(float(m[dom]), 2))
    elif g == 8:
        top = ids[np.argmax(co[ids][:, 2])]
        m = copy(top); m[ARMS] = 0
        new = np.tile(norm(m), (len(ids), 1))
    else:
        new = np.zeros_like(C); new[:, gi['B_Head']] = 1
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    count[g] = count.get(g, 0) + 1
# smooth the mantle cards inside each card (3 passes over the card's own edges)
mant = gv == 1
E = edges[mant[edges[:, 0]] & mant[edges[:, 1]]]
for _ in range(3):
    acc = Wt.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    Wt[mant] = (acc / deg[:, None])[mant]
print('RULE pieces per garment', count)
arm_on_mantle = Wt[mant][:, ARMS].sum(1)
print('RULE mantle arm share max', round(float(arm_on_mantle.max()), 3), 'leg share max', round(float(Wt[mant][:, LEGS].sum(1).max()), 3))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
