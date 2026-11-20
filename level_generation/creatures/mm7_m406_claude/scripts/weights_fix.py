"""m406 weight rules, by garment (scripts/garments.py 'garment' attribute):
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/neck free of the shoulders.
             The tabard is part of the torso shell (P01): below the belt its flaps blend into the strip rule (B_Pelvis
             at the belt -> the thigh at the hem, the left/right mix per vertex by its x), fully at 6 cm under the belt;
             no arm weight on the shell below the armpits.
1 head       helmet and eyes rigid on B_Head.
3 coif       mail coif: copy of the skin under it (4 nearest, inverse distance), no arm or clavicle weight.
4 fittings   belt buckle and knee-cop studs: rigid on the bone that dominates the skin under them.
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
ARMS = idx(('UpperArm', 'Forearm', 'Hand', 'Finger'))
CLAV = idx(('Clavicle',))
PEL = gi['B_Pelvis']
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
print('RULE skin jaw free of the shoulders: vertices changed', neck_moved)
# torso shell (P01): no arm weight below the armpit band; tabard flaps below the belt -> strip rule
tor = np.where(pv == 1)[0]
low = tor[co[tor, 2] < J('B_Spine2')[2]]
Wt[np.ix_(low, ARMS)] = 0
belt = float(co[pv == 11][:, 2].mean()) if (pv == 11).any() else J('B_Pelvis')[2]
flap = tor[co[tor, 2] < belt]
if len(flap):
    z = co[flap, 2]; bot = z.min()
    a = np.clip((belt - z) / max(belt - bot, 1e-3), 0, 1)
    wl = np.clip(0.5 + co[flap, 0] / 0.12, 0, 1)
    strip = np.zeros((len(flap), len(names))); strip[:, PEL] = 1 - a
    strip[:, gi['B_L_Thigh']] = a * wl; strip[:, gi['B_R_Thigh']] = a * (1 - wl)
    blend = np.clip((belt - z) / 0.06, 0, 1)[:, None]
    Wt[flap] = Wt[flap] * (1 - blend) + strip * blend
print('RULE torso shell: no arm weight on', len(low), 'vertices; tabard flaps strip-weighted', len(flap), 'below z', round(belt, 3))
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()


def copy(i):
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    return (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()


count = {}
for p in sorted(set(pv[gv != 0].tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    if g == 1:
        new = np.zeros((len(ids), len(names))); new[:, gi['B_Head']] = 1
    elif g == 3:
        new = np.array([copy(i) for i in ids]); new[:, ARMS] = 0; new[:, CLAV] = 0
    else:
        C = np.array([copy(i) for i in ids]); dom = int(np.argmax(C.mean(0)))
        new = np.zeros_like(C); new[:, dom] = 1
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
