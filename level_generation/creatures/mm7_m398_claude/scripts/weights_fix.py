"""m398 weight rules by piece (garments.py classes), applied to the Meshy-transferred weights right after build_rig.py
(before the twist bones split the arm weights). The skeleton is separate rigid pieces with air between them, so no
weight may reach across a gap (batch note: thin limbs, visible gaps between bones):
- torso chain: cuirass, ribs, clavicle ring, back/pelvis bones and the spine column take smooth weights along the
  spine chain by height (B_Pelvis .. B_Head; each child joint ramps in over +-R around its height; the cuirass uses a
  wider ramp so the plate bends softly); no arm or leg weight;
- arm bones: shoulder ball and humerus on B_UpperArm, below the elbow joint (projection along the arm, +-2 cm ramp)
  on B_Forearm; elbow knob on B_Forearm;
- leg bones: femur/tibia piece on B_Thigh above the knee and B_Calf below (+-3 cm ramp); kneecap half/half; fibula
  on B_Calf;
- gauntlet: Meshy's weights limited to its own side's upper arm, forearm and hand (fingers come in
  finger_weights.py); boots: limited to their own side's calf, foot and toe; breeches: limited to pelvis, spine and
  both thighs/calves, smoothed 2 passes along the cloth's edges;
- skull, helmet, teeth, helmet rivets: rigid B_Head;
- studs/rivets of the body: rigid on the mean final weights of the nearest vertices of other pieces.
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
J = lambda n: np.array(rig.data.bones[n].head_local)
CHAIN = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
ZJ = [J(n)[2] for n in CHAIN]


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def chain(z, r):
    t = [np.ones_like(z)] + [ss((z - (zj - r)) / (2 * r)) for zj in ZJ[1:]] + [np.zeros_like(z)]
    W = np.zeros((len(z), len(names)))
    for k, n in enumerate(CHAIN):
        W[:, gi[n]] = t[k] * (1 - t[k + 1])
    return W


def along(ids, a, b, r):
    """share of the child joint b for vertices ids, projected on the a -> b segment (ramp +-r around b)"""
    A, Bj = J(a), J(b); d = (Bj - A) / np.linalg.norm(Bj - A)
    return ss(((co[ids] - Bj) @ d + r) / (2 * r))


def keep(ids, bones):
    W = np.zeros((len(ids), len(names)))
    for n in bones:
        W[:, gi[n]] = Wt[ids, gi[n]]
    s = W.sum(1)
    return W / np.maximum(s, 1e-9)[:, None], int((s < 1e-6).sum())


NEW = np.zeros_like(Wt); done = np.zeros(nv, bool)
SIDE = {'L': {'humerus': 18, 'ball': 23, 'knob': 19, 'leg': 12, 'patella': 22, 'fibula': 30, 'glove': 2, 'boot': 5},
        'R': {'humerus': 16, 'ball': 24, 'knob': 20, 'leg': 13, 'patella': 21, 'fibula': 29, 'glove': 1, 'boot': 6}}
LIMB = {p for P in SIDE.values() for k, p in P.items() if k not in ('glove', 'boot')}
# torso chain
for p in sorted(set(pv[gv == 0].tolist()) - LIMB) + [0]:
    ids = np.where(pv == p)[0]
    NEW[ids] = chain(co[ids, 2], 0.06 if p == 0 else 0.03); done[ids] = True
for s, P in SIDE.items():
    ids = np.where(np.isin(pv, (P['humerus'], P['ball'])))[0]
    t = along(ids, f'B_{s}_UpperArm', f'B_{s}_Forearm', 0.02)
    NEW[ids, gi[f'B_{s}_UpperArm']] = 1 - t; NEW[ids, gi[f'B_{s}_Forearm']] = t; done[ids] = True
    ids = np.where(pv == P['knob'])[0]; NEW[ids, gi[f'B_{s}_Forearm']] = 1; done[ids] = True
    ids = np.where(pv == P['leg'])[0]
    t = along(ids, f'B_{s}_Thigh', f'B_{s}_Calf', 0.03)
    NEW[ids, gi[f'B_{s}_Thigh']] = 1 - t; NEW[ids, gi[f'B_{s}_Calf']] = t; done[ids] = True
    ids = np.where(pv == P['patella'])[0]; NEW[ids, gi[f'B_{s}_Thigh']] = 0.5; NEW[ids, gi[f'B_{s}_Calf']] = 0.5; done[ids] = True
    ids = np.where(pv == P['fibula'])[0]; NEW[ids, gi[f'B_{s}_Calf']] = 1; done[ids] = True
    ids = np.where(pv == P['glove'])[0]
    NEW[ids], z = keep(ids, [f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand']); done[ids] = True
    if z:
        NEW[ids[NEW[ids].sum(1) < 1e-6], gi[f'B_{s}_Hand']] = 1
    print('RULE gauntlet', s, 'vertices without arm weight', z)
    ids = np.where(pv == P['boot'])[0]
    NEW[ids], z = keep(ids, [f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe0']); done[ids] = True
    print('RULE boot', s, 'vertices without leg weight', z)
ids = np.where(gv == 3)[0]
NEW[ids], z = keep(ids, ['B_Pelvis', 'B_Spine', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf']); done[ids] = True
if z:
    NEW[ids[NEW[ids].sum(1) < 1e-6], gi['B_Pelvis']] = 1
edges = np.array([tuple(e.vertices) for e in me.edges])
br = gv == 3; E = edges[br[edges[:, 0]] & br[edges[:, 1]]]
for _ in range(2):
    acc = NEW.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], NEW[E[:, 1]]); np.add.at(acc, E[:, 1], NEW[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    NEW[br] = (acc / deg[:, None])[br]
print('RULE breeches: vertices without pelvis/leg weight', z, 'arm share before', round(float(Wt[ids][:, [gi[n] for n in names if 'Arm' in n or 'Hand' in n or 'Finger' in n]].sum(1).max()), 3))
ids = np.where(np.isin(gv, (5, 6, 7)))[0]; NEW[ids, gi['B_Head']] = 1; done[ids] = True
# studs: mean of the nearest 6 vertices of other (already ruled) pieces
ref = np.where(done)[0]
kd = KDTree(len(ref))
for i, r in enumerate(ref):
    kd.insert(co[r], i)
kd.balance()
studs = sorted(set(pv[~done].tolist()))
for p in studs:
    ids = np.where(pv == p)[0]; acc = np.zeros(len(names))
    for i in ids:
        for c, j, d in kd.find_n(co[i], 6):
            acc += NEW[ref[j]]
    NEW[ids] = acc / acc.sum()
print('RULE studs rigid', len(studs), 'pieces')
NEW /= np.maximum(NEW.sum(1, keepdims=True), 1e-9)
# gap check: a vertex weighted to an arm bone must be on an arm piece, to a leg bone on a leg/breeches/boot piece
ARMB = [gi[n] for n in names if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
LEGB = [gi[n] for n in names if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
armp = np.isin(pv, [P[k] for P in SIDE.values() for k in ('humerus', 'ball', 'knob', 'glove')])
legp = np.isin(pv, [P[k] for P in SIDE.values() for k in ('leg', 'patella', 'fibula', 'boot')]) | (gv == 3)
print('G4GAP arm weight off the arm pieces', int(((NEW[:, ARMB].sum(1) > 1e-3) & ~armp).sum()),
      'leg weight off the leg pieces', int(((NEW[:, LEGB].sum(1) > 1e-3) & ~legp & (gv != 8)).sum()))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(NEW[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(NEW[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
