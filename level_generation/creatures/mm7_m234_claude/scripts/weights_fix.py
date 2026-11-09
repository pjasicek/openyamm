"""m150 weight rules (adapted from mm7_m406_claude), by garment (scripts/garments.py 'garment' attribute):
0 skin       Meshy weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/neck free of the shoulders.
             No arm weight on the trunk below B_Spine2 inside the shoulders.
1 head       crest, helmet back plate, temple ornaments and eyes rigid on B_Head.
3 copy       helmet bowl + hair, straps, belt, sandals, knee plates: copy of the skin under it (4 nearest, inverse
             distance), no arm or clavicle weight.
4 fittings   buckle, belt rings, studs: rigid on the bone that dominates the skin under them.
6 skirt      dress: B_Pelvis at the belt -> SKIRT_SHARE on the thighs at the hem, left/right mix per vertex by x.
7 tabs       each leather tab a strip: B_Pelvis at the belt -> TAB_SHARE on the thighs at its tip, ONE left/right
             mix per tab from its centre x.
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
# skin below the armpits carries no arm weight (Meshy spreads the upper arm onto the flank of the breastplate)
tor = np.where((pv == 0))[0]
def seg_dist(p, a, b):
    t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * (b - a)), axis=1)
far = np.ones(len(tor), bool)
for s_ in ('L', 'R'):
    far &= seg_dist(co[tor], J(f'B_{s_}_UpperArm'), J(f'B_{s_}_Forearm')) > 0.075
low = tor[(co[tor, 2] < J('B_Spine2')[2]) & (np.abs(co[tor, 0]) < np.abs(J('B_R_UpperArm')[0]) - 0.02) & far]
Wt[np.ix_(low, ARMS)] = 0
print('RULE skin: no arm weight on', len(low), 'trunk vertices below B_Spine2')
belt = J('B_Pelvis')[2] + float(os.environ.get('BELT_DZ', '0.07'))
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
LEG = [gi[n] for n in names if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]


def dress(ids, share, mix_x=None):
    """pelvis at the belt -> `share` on the thighs at the hem; left/right mix per vertex by x, or one mix for all"""
    z = co[ids, 2]; bot = z.min()
    a = np.clip((belt - z) / max(belt - bot, 1e-3), 0, 1) * share
    x = co[ids, 0] if mix_x is None else np.full(len(ids), mix_x)
    wl = np.clip(0.5 + x / 0.12, 0, 1)
    new = np.zeros((len(ids), len(names))); new[:, PEL] = 1 - a
    new[:, gi['B_L_Thigh']] = a * wl; new[:, gi['B_R_Thigh']] = a * (1 - wl)
    return new
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
    elif g == 6:
        new = dress(ids, float(os.environ.get('SKIRT_SHARE', '0.45')))
    elif g == 7:
        new = dress(ids, float(os.environ.get('TAB_SHARE', '0.6')), mix_x=float(co[ids, 0].mean()))
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
