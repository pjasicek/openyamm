"""m470 weight rules by piece (garments.py), applied to the Meshy-transferred weights right after build_rig.py (before
the twist bones):
- skin (P00): Meshy's weights + shoulder fade (upper arm -> clavicle over 7 cm medially) + jaw/head skin free of the
  clavicles and upper arms (mm6_natm_claude/mm6_gob2_claude rules);
- hair (P01, the mane falls to the upper back): B_Head above the head joint, blending to B_Neck and then B_Spine2 /
  B_Spine1 down the back by height, no arm weight;
- teeth and eyes: rigid B_Head;
- chest lacing bars and eyelet studs: rigid on the mean final weights of the 6 nearest skin vertices.
Prints a gap check (arm weight on the hair/torso studs). Args: -- <in blend> <out blend>"""
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


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


skin = np.where(gv == 0)[0]
moved = 0
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    m = (co[skin] - sh) @ d
    sel = (m < 0) & (Wt[skin, ua] > 0)
    keep = np.clip(1.0 + m / 0.07, 0, 1)
    dw = Wt[skin, ua] * (1 - keep) * sel
    Wt[skin, ua] -= dw; Wt[skin, cv] += dw; moved += int((dw > 1e-3).sum())
print('RULE skin shoulder fade: vertices changed', moved)
jz = J('B_Head')[2] - 0.02; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm'))]
fz = np.clip((co[skin, 2] - (jz - 0.03)) / 0.03, 0, 1)
r = fz * (1 - np.clip((np.abs(co[skin, 0] - ax_x) - 0.07) / 0.07, 0, 1))
dw = Wt[np.ix_(skin, SH)].sum(1) * r
Wt[np.ix_(skin, SH)] *= (1 - r)[:, None]
tgt = np.where(co[skin, 2] > jz, gi['B_Head'], gi['B_Neck'])
np.add.at(Wt, (skin, tgt), dw)
print('RULE skin jaw free of the shoulders: vertices changed', int((dw > 1e-4).sum()))
NEW = Wt.copy()
hair = np.where(gv == 1)[0]
zH, zN, zS2, zS1 = J('B_Head')[2], J('B_Neck')[2], J('B_Spine2')[2], J('B_Spine1')[2]
z = co[hair, 2]
W = np.zeros((len(hair), len(names)))
th = ss((z - zN) / max(zH - zN, 1e-3)); tn = ss((z - zS2) / max(zN - zS2, 1e-3)); ts = ss((z - zS1) / max(zS2 - zS1, 1e-3))
W[:, gi['B_Head']] = th; W[:, gi['B_Neck']] = (1 - th) * tn; W[:, gi['B_Spine2']] = (1 - th) * (1 - tn) * ts
W[:, gi['B_Spine1']] = (1 - th) * (1 - tn) * (1 - ts)
NEW[hair] = W
ids = np.where(np.isin(gv, (2, 3)))[0]; NEW[ids] = 0; NEW[ids, gi['B_Head']] = 1
kd = KDTree(len(skin))
for i, s_ in enumerate(skin):
    kd.insert(co[s_], i)
kd.balance()
studs = sorted(set(pv[np.isin(gv, (4, 5))].tolist()))
for p in studs:
    ids = np.where(pv == p)[0]; acc = np.zeros(len(names))
    for i in ids:
        for c, j, d in kd.find_n(co[i], 6):
            acc += Wt[skin[j]]
    NEW[ids] = acc / acc.sum()
print('RULE hair vertices', len(hair), 'studs/lacing rigid', len(studs), 'pieces')
NEW /= np.maximum(NEW.sum(1, keepdims=True), 1e-9)
ARMB = [gi[n] for n in names if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
print('G4GAP arm weight > 0.05 on the hair', int((NEW[hair][:, ARMB].sum(1) > 0.05).sum()),
      'on the chest lacing', int((NEW[gv == 4][:, ARMB].sum(1) > 0.05).sum()))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(NEW[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(NEW[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
