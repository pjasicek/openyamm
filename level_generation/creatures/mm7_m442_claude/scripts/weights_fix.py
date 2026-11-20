"""m442 weight rules, by garment (scripts/garments.py 'garment' attribute); bar1's armour rules + gob2/natm ones:
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/neck free of the shoulders.
1 head       hair, face strands and eyes rigid on B_Head.
2 yoke       shoulder yoke: per-vertex copy of the skin under it (4 nearest, inverse distance), arm share capped at
             0.35 (excess to the clavicle) so the stiff leather rides the shoulders, then smoothed 3 passes.
3 ponytail   B_Head above the nape, ramping to B_Neck and then B_Spine2 toward its tip (by height), no arm weight.
4 straps     belt, chest strap, buckle plate, thigh straps: copy of the skin under them, no arm weight (thigh straps
             keep their leg weights through the copy).
5 scabbard   the sword scabbard on the back: rigid on B_Spine2.
6 dagger     dagger sheath and hilt on the right hip: rigid on B_Pelvis.
7 fittings   studs, spikes, buckles: rigid on the bone that dominates the skin under them.
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
PEL = gi['B_Pelvis']
skin = np.where(gv == 0)[0]

# skin rules ---------------------------------------------------------------------------------------------------------
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

# m442 (m342 lesson): the wide blouse sleeves are part of the skin shell; hanging beside the hips in the A-pose they
# take pelvis/leg weight from Meshy at the hem. Arm-dominated skin vertices (own arm share > 0.5) give their pelvis,
# lower-spine and leg weight to their own arm bones, proportionally
LOWB = [gi[n] for n in names if n in ('B_Pelvis', 'B_Spine', 'B_Spine1') or any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
freed = 0
for s_ in 'LR':
    own = ARM[s_]
    m_ = skin[(Wt[skin][:, own].sum(1) > 0.5) & (np.sign(co[skin, 0]) == (1 if s_ == 'L' else -1))]
    for i in m_:
        lw = Wt[i, LOWB].sum()
        if lw > 1e-4:
            Wt[i, own] += lw * Wt[i, own] / Wt[i, own].sum(); Wt[i, LOWB] = 0; freed += 1
print('RULE sleeve skin freed of pelvis/lower spine/legs', freed)
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()


def copy(i):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()


def rigid(n, k):
    w = np.zeros((n, len(names))); w[:, gi[k]] = 1; return w


count = {}
nape, base = J('B_Head')[2] - 0.03, J('B_Neck')[2] - 0.06
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    if g == 1:
        new = rigid(len(ids), 'B_Head')
    elif g == 2:
        C = np.array([copy(i) for i in ids])
        for s in 'LR':
            a = C[:, ARM[s]].sum(1); over = np.clip(a - 0.35, 0, None)
            sc = np.where(a > 1e-9, (a - over) / np.maximum(a, 1e-9), 1)
            C[:, ARM[s]] *= sc[:, None]; C[:, gi[f'B_{s}_Clavicle']] += over
        new = C
    elif g == 3:
        z = co[ids][:, 2]
        t1 = np.clip((nape - z) / 0.06, 0, 1)               # head -> neck just below the nape
        t2 = np.clip((nape - 0.06 - z) / max(nape - 0.06 - base, 0.02), 0, 1)   # neck -> chest toward the tip
        new = np.zeros((len(ids), len(names)))
        new[:, gi['B_Head']] = 1 - t1; new[:, gi['B_Neck']] = t1 * (1 - t2); new[:, gi['B_Spine2']] = t1 * t2
    elif g == 4:
        C = np.array([copy(i) for i in ids]); C[:, ARMS] = 0
        new = C
    elif g == 5:
        new = rigid(len(ids), 'B_Spine2')
    elif g == 6:
        new = rigid(len(ids), 'B_Pelvis')
    else:
        C = np.array([copy(i) for i in ids]); m = C.mean(0); dom = int(np.argmax(m))
        new = np.zeros_like(C); new[:, dom] = 1
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    count[g] = count.get(g, 0) + 1
# smooth the yoke inside its own edges
edges = np.array([tuple(e.vertices) for e in me.edges])
yk = gv == 2
E = edges[yk[edges[:, 0]] & yk[edges[:, 1]]]
for _ in range(3):
    acc = Wt.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    Wt[yk] = (acc / deg[:, None])[yk]
print('RULE pieces per garment', count, 'yoke arm share max', round(float(Wt[yk][:, ARMS].sum(1).max()), 3) if yk.any() else None)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
