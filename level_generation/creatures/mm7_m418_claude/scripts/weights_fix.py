"""m418 weight rules by piece (garments.py), applied to the bone-heat weights of build_rig.py (WEIGHTS=auto) before
the twist bones:
- skin (P00): bone heat, with
  - unweighted skin vertices (bone heat leaves some on thin parts) filled from their weighted edge neighbours;
  - the claws rigid: every skin vertex past the wrist along the forearm (within the hand's reach) is 100 % B_*_Hand;
  - no arm weight below the elbows' height outside the arms (legs, belly) and no leg weight on the arms (the hands
    hang near the knees): a vertex keeps the arm or the leg chain, whichever its nearest bone belongs to;
  - the hood (in front of the rim groove, y < -0.98 at the working scale, above the shoulders) rigid on B_Head;
    the groove blends B_Head -> B_Neck over 8 cm;
- teeth (garment 1): rigid B_Head;
- tail spines (garment 2): rigid on the mean final weights of the 6 nearest skin vertices.
Prints a gap check (arm weight on the legs, leg weight on the arms). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
J = lambda n: np.array(rig.data.bones[n].head_local)
T = lambda n: np.array(rig.data.bones[n].tail_local)
skin = gv == 0
# ---- fill unweighted skin from neighbours (repeat until none left)
E = np.array([tuple(e.vertices) for e in me.edges])
E = E[skin[E[:, 0]] & skin[E[:, 1]]]
empty = skin & (Wt.sum(1) < 1e-6)
n0 = int(empty.sum())
for _ in range(200):
    if not empty.any():
        break
    acc = np.zeros_like(Wt); cnt = np.zeros(nv)
    for a, b in ((0, 1), (1, 0)):
        ok = ~empty[E[:, b]] & empty[E[:, a]]
        np.add.at(acc, E[ok, a], Wt[E[ok, b]] / np.maximum(Wt[E[ok, b]].sum(1, keepdims=True), 1e-9)); np.add.at(cnt, E[ok, a], 1)
    got = empty & (cnt > 0)
    Wt[got] = acc[got] / cnt[got, None]; empty &= ~got
print('RULE filled unweighted skin vertices', n0, 'left', int(empty.sum()))
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)


def seg_dist(p, a, b):
    d = b - a; t = np.clip((p - a) @ d / (d @ d), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, d)), axis=1)


ARM = {s: [f'B_{s}_Clavicle', f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand'] for s in 'LR'}
LEG = {s: [f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe0'] for s in 'LR'}
ARMB = [gi[n] for s in 'LR' for n in ARM[s][1:]]
LEGB = [gi[n] for s in 'LR' for n in LEG[s]]
# nearest bone segment per vertex among the limbs
dist_arm = np.min([seg_dist(co, J(n), T(n) if 'Hand' not in n else J(n) + (J(n) - J(n.replace('Hand', 'Forearm'))) * 1.4)
                   for s in 'LR' for n in ARM[s][1:]], axis=0)
dist_leg = np.min([seg_dist(co, J(n), T(n)) for s in 'LR' for n in LEG[s]], axis=0)
TORSO = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck']
HOOD_TIP = np.array([-0.075, -1.45, 1.1])                         # the head bone is a short leaf: the hood's own axis
dist_torso = np.minimum(np.min([seg_dist(co, J(n), T(n)) for n in TORSO], axis=0), seg_dist(co, J('B_Head'), HOOD_TIP))
on_arm = skin & (dist_arm < np.minimum(dist_leg, dist_torso))
moved_leg = Wt[on_arm][:, LEGB].sum(1); moved_arm = Wt[skin & ~on_arm][:, ARMB].sum(1)
Wt[np.ix_(on_arm, LEGB)] = 0                                      # arms: no leg weight
low = skin & ~on_arm & (co[:, 2] < 0.85)
Wt[np.ix_(low, ARMB)] = 0                                         # legs and belly below the elbows: no arm weight
# the hump and its dorsal spines: no upper-arm/forearm/hand weight where a spine/neck/head bone is nearer than the arm
# arm weight fades out over 6 cm where the torso/hood axis is nearer than the arm's (hood rim, hump, dorsal spines)
fade = np.clip((dist_torso - dist_arm) / 0.06 + 0.5, 0, 1)
back = skin & ~on_arm
Wt[np.ix_(back, ARMB)] *= fade[back, None]
print('RULE torso: arm weight faded on', int((back & (fade < 1)).sum()), 'hump/hood vertices')
print('RULE limb split: leg weight removed from', int((moved_leg > 0.01).sum()), 'arm vertices; arm weight removed from',
      int((Wt[low].sum(1) < 0.999).sum()), 'leg/belly vertices')
# claws rigid on the hand
for s in 'LR':
    w, f = J(f'B_{s}_Hand'), J(f'B_{s}_Forearm')
    d = (w - f) / np.linalg.norm(w - f)
    m = skin & on_arm & ((co - w) @ d > 0.0) & (np.linalg.norm(co - w, axis=1) < 0.5) & (np.sign(co[:, 0] + 0.075) == np.sign(w[0] + 0.075))
    Wt[m] = 0; Wt[m, gi[f'B_{s}_Hand']] = 1
    print('RULE', s, 'hand rigid vertices', int(m.sum()))
# hood rigid on the head, blended over the groove
Y_RIM = -0.98
hood_t = np.clip((Y_RIM - co[:, 1]) / 0.08 + 0.5, 0, 1)
hm = skin & ~on_arm & (co[:, 1] < Y_RIM + 0.04) & (co[:, 2] > 0.85) & (dist_torso < dist_arm)
Wt[hm] *= (1 - hood_t[hm])[:, None]
Wt[hm, gi['B_Head']] += hood_t[hm]
Wt[gv == 1] = 0; Wt[gv == 1, gi['B_Head']] = 1
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
# spines from the skin under them
idx = np.where(skin)[0]
kd = KDTree(len(idx))
for k, i in enumerate(idx):
    kd.insert(co[i], k)
kd.balance()
for i in np.where(gv == 2)[0]:
    nb = [idx[h[1]] for h in kd.find_n(co[i], 6)]
    Wt[i] = Wt[nb].mean(0)
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
# keep the 4 strongest influences
for i in range(nv):
    r = np.argsort(Wt[i])[::-1]
    Wt[i, r[4:]] = 0
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for j, n in enumerate(names):
    g = body.vertex_groups[n]
    for i in np.where(Wt[:, j] > 1e-4)[0]:
        g.add([int(i)], float(Wt[i, j]), 'REPLACE')
print('G4GAP arm weight > 0.05 on leg-side skin', int((Wt[skin & ~on_arm & (co[:, 2] < 0.85)][:, ARMB].sum(1) > 0.05).sum()),
      '; leg weight > 0.05 on arm skin', int((Wt[on_arm][:, LEGB].sum(1) > 0.05).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
