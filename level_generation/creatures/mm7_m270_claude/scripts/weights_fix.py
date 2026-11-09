"""m270 weight rules by piece (garments.py), applied to the Meshy-transferred weights right after build_rig.py (before
the twist bones). The lich is separate pieces (built mirrored: +X is its left in this build):
- plate (breastplate P07, abdomen P11), gold belt (P14, buckle P15, band P21): smooth weights along the spine chain
  by height (B_Pelvis .. B_Spine2; wide ramps so the plates bend softly), no arm or leg weight;
- pauldrons (P08 left, P09 right) and the chain shoulder caps (P19 left, P20 right): rigid on the mean of Meshy's
  weights limited to that side's clavicle and upper arm plus B_Spine2;
- arm pieces (P01 left, P02 right: chain sleeve and bony hand) and wrist cuffs (P12 left, P13 right): Meshy's
  weights limited to their own arm (fingers come in finger_weights.py);
- legs and shoes (P04): Meshy's weights limited to the pelvis and the legs, left/right by side;
- chain skirt (P05): a dress (B_Pelvis at the hips -> LEG_MAX of leg weight at the hem, one smooth left/right mix,
  thigh/calf by height), smoothed along its edges; skirt_bones.py later moves its pelvis share onto skirt bones;
- head pieces (the grafted skull, crown and coif, ids 100+): B_Head above the head joint, blending to B_Neck and
  B_Spine2 down the coif's neck.
Prints a gap check (arm weight off the arms/cuffs/shoulders, leg weight off the legs/skirt). Args: -- <in> <out>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
LEG_MAX = float(os.environ.get('LEG_MAX', '0.85'))   # 0.45 let the striding legs split the skirt
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
J = lambda n: np.array(rig.data.bones[n].head_local)
idx = lambda keys: [gi[n] for n in names if any(k in n for k in keys)]
ARMNC = {s: idx((f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'B_{s}_Finger')) for s in 'LR'}
LEG = {s: idx((f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe')) for s in 'LR'}
CHAIN = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2']
ZJ = [J(n)[2] for n in CHAIN]


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def chain(z, r):
    t = [np.ones_like(z)] + [ss((z - (zj - r)) / (2 * r)) for zj in ZJ[1:]] + [np.zeros_like(z)]
    W = np.zeros((len(z), len(names)))
    for k, n in enumerate(CHAIN):
        W[:, gi[n]] = t[k] * (1 - t[k + 1])
    return W


def keep(rows, cols):
    W = np.zeros((len(rows), len(names))); W[:, cols] = Wt[np.ix_(rows, cols)]
    s = W.sum(1); return W / np.maximum(s, 1e-9)[:, None], s < 1e-6


NEW = Wt.copy(); done = np.zeros(nv, bool)
for p in (7, 11, 14, 15, 21):
    ids = np.where(pv == p)[0]; NEW[ids] = chain(co[ids, 2], 0.06); done[ids] = True
for s, pl, cap, arm, cuff in (('L', 8, 19, 1, 12), ('R', 9, 20, 2, 13)):
    for p in (pl, cap):
        ids = np.where(pv == p)[0]
        W, z = keep(ids, [gi[f'B_{s}_Clavicle'], gi[f'B_{s}_UpperArm'], gi['B_Spine2']])
        m = W.mean(0); NEW[ids] = m / m.sum(); done[ids] = True
        print('RULE shoulder piece', p, s, {names[j]: round(float(m[j]), 2) for j in np.nonzero(m > 0.05)[0]})
    for p in (arm, cuff):
        ids = np.where(pv == p)[0]; W, z = keep(ids, ARMNC[s]); W[z, gi[f'B_{s}_Hand']] = 1; NEW[ids] = W; done[ids] = True
        print('RULE arm piece', p, s, 'vertices without arm weight', int(z.sum()))
ids = np.where(pv == 4)[0]
W = np.zeros((len(ids), len(names)))
for s, sg in (('L', 1), ('R', -1)):
    side = np.sign(co[ids, 0]) == sg
    cols = LEG[s] + [gi['B_Pelvis']]
    W[np.ix_(side, cols)] = Wt[np.ix_(ids[side], cols)]
z = W.sum(1) < 1e-6; W[z, gi['B_Pelvis']] = 1; NEW[ids] = W / W.sum(1, keepdims=True); done[ids] = True
print('RULE legs: vertices without leg weight', int(z.sum()))
ids = np.where(pv == 5)[0]; Q = co[ids]
zh = J('B_L_Thigh')[2]
depth = ss((zh - Q[:, 2]) / max(zh - 0.05, 1e-3)); leg = depth * LEG_MAX
wl = ss((Q[:, 0] + 0.12) / 0.24); kz = J('B_L_Calf')[2]; calf = ss((kz + 0.1 - Q[:, 2]) / 0.3) * 0.4
W = np.zeros((len(ids), len(names))); W[:, gi['B_Pelvis']] = 1 - leg
for s, w in (('L', wl), ('R', 1 - wl)):
    W[:, gi[f'B_{s}_Thigh']] = leg * w * (1 - calf); W[:, gi[f'B_{s}_Calf']] = leg * w * calf
above = Q[:, 2] > zh                                     # the skirt's top under the belt follows the spine chain
W[above] = chain(Q[above, 2], 0.06)
NEW[ids] = W; done[ids] = True
edges = np.array([tuple(e.vertices) for e in me.edges])
sk = pv == 5; E = edges[sk[edges[:, 0]] & sk[edges[:, 1]]]
for _ in range(3):
    acc = NEW.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], NEW[E[:, 1]]); np.add.at(acc, E[:, 1], NEW[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    NEW[sk] = (acc / deg[:, None])[sk]
ids = np.where(pv >= 100)[0]
zh_, zn = J('B_Head')[2], J('B_Neck')[2]
th = ss((co[ids, 2] - zn) / max(zh_ - zn, 1e-3)); tn = ss((co[ids, 2] - (zn - 0.05)) / 0.05)
W = np.zeros((len(ids), len(names)))
W[:, gi['B_Head']] = th; W[:, gi['B_Neck']] = (1 - th) * tn; W[:, gi['B_Spine2']] = (1 - th) * (1 - tn)
NEW[ids] = W; done[ids] = True
rest = np.where(~done)[0]
print('RULE pieces left on Meshy weights', sorted(set(pv[rest].tolist())))
NEW /= np.maximum(NEW.sum(1, keepdims=True), 1e-9)
ARMB = idx(('UpperArm', 'Forearm', 'Hand', 'Finger')); LEGB = idx(('Thigh', 'Calf', 'Foot', 'Toe'))
armok = np.isin(pv, (1, 2, 8, 9, 12, 13, 19, 20)); legok = np.isin(pv, (4, 5))
print('G4GAP arm weight > 0.05 off the arm/shoulder pieces', int(((NEW[:, ARMB].sum(1) > 0.05) & ~armok).sum()),
      'leg weight > 0.05 off the legs/skirt', int(((NEW[:, LEGB].sum(1) > 0.05) & ~legok).sum()))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(NEW[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(NEW[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
