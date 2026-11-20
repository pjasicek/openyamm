"""m178 weight rules by piece (garments.py), applied to the bone-heat weights of build_rig.py (WEIGHTS=auto; joints
measured on the mesh, the head bone 17 cm long so the heat reaches the skull spikes) before the twist bones:
- skin (P00): bone heat, with
  - unweighted skin vertices filled from their weighted edge neighbours;
  - the hands rigid: every skin vertex past the wrist along the forearm (within the hand's 0.6 m reach) is 100 %
    B_*_Hand (the long clawed fingers keep their shape; no finger weights);
  - no arm weight on the legs/belly and no leg weight on the arms (the hands hang beside the thighs): a vertex keeps the
    arm or the leg chain, whichever its nearest bone belongs to;
  - the shoulder spikes and the trapezius above the shoulder joint: upper-arm weight moved to the clavicle (fading in
    over 5 cm above the joint), so a raised arm does not shear the spikes; arm weight fades out where the trunk/head
    axis is nearer than the arm's (back spikes);
  - the head (above the neck joint, inside the skull) rigid on B_Head, blended B_Neck -> B_Head over 6 cm;
- teeth and eyes (garments 1, 3): rigid B_Head;
- tail spikes (garment 2): rigid on the mean final weights of the 6 nearest skin vertices.
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
TORSO = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
dist_torso = np.min([seg_dist(co, J(n), T(n)) for n in TORSO], axis=0)
on_arm = skin & (dist_arm < np.minimum(dist_leg, dist_torso))
# m178: the long fingers curl in beside the thighs, where a leg bone can be nearer than the hand: the hand is the skin
# component beyond the wrist plane (edge connectivity), forced onto the arm and made rigid below
HAND = {}
for s_ in 'LR':
    w, f = J(f'B_{s_}_Hand'), J(f'B_{s_}_Forearm')
    d = (w - f) / np.linalg.norm(w - f)
    beyond = skin & ((co - w) @ d > 0.0) & (np.linalg.norm(co - w, axis=1) < 0.7)
    seed = int(np.argmin(np.where(beyond, np.linalg.norm(co - (w + d * 0.08), axis=1), 9)))
    reg = np.zeros(nv, bool); reg[seed] = True
    EB = E[beyond[E[:, 0]] & beyond[E[:, 1]]]
    for _ in range(400):
        nxt = reg.copy(); nxt[EB[reg[EB[:, 0]], 1]] = True; nxt[EB[reg[EB[:, 1]], 0]] = True
        if (nxt == reg).all():
            break
        reg = nxt
    HAND[s_] = reg; on_arm |= reg
    print('RULE', s_, 'hand component beyond the wrist plane:', int(reg.sum()), 'vertices, lowest z', round(float(co[reg, 2].min()), 3))
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
    m = HAND[s]
    Wt[m] = 0; Wt[m, gi[f'B_{s}_Hand']] = 1
    print('RULE', s, 'hand rigid vertices', int(m.sum()))
# shoulder spikes / trapezius: upper-arm weight -> clavicle above the shoulder joint
for s_ in 'LR':
    sh = J(f'B_{s_}_UpperArm')
    up = np.clip((co[:, 2] - sh[2] - 0.01) / 0.05, 0, 1) * (np.sign(co[:, 0]) == np.sign(sh[0])) * skin
    ua, cv = gi[f'B_{s_}_UpperArm'], gi[f'B_{s_}_Clavicle']
    dw = Wt[:, ua] * up
    Wt[:, ua] -= dw; Wt[:, cv] += dw
    print('RULE', s_, 'shoulder top: upper-arm weight moved to the clavicle on', int((dw > 0.01).sum()), 'vertices')
# spikes, ear tips, toe claws and heel spurs rigid on the skin under their base (the stretch gate found the shoulder
# and back spikes sheared up to 9.7x between clavicle, spine, neck and head weights): a spike is a thin protrusion,
# measured by the inward thickness (ray cast along -normal and three tilted directions); seeds thinner than 3.5 cm,
# grown through edges while thinner than 6 cm, outside the hands and the tail; each connected spike takes the mean
# weights of its base ring (the unflagged edge neighbours)
from mathutils.bvhtree import BVHTree
from mathutils import Vector as _V
_skf = [tuple(p.vertices) for p in me.polygons if gv[p.vertices[0]] == 0]
_tree = BVHTree.FromPolygons([tuple(c) for c in co], _skf)
th = np.ones(nv)
for v in me.vertices:
    if gv[v.index] != 0:
        continue
    n = v.normal; o = v.co - n * 0.002
    for d in (-n, (-n + _V((0.3, 0, 0))).normalized(), (-n + _V((0, 0.3, 0))).normalized(), (-n + _V((0, 0, 0.3))).normalized()):
        loc, nrm, idx, dist = _tree.ray_cast(o, d, 1.0)
        if loc is not None:
            th[v.index] = min(th[v.index], dist)
excl = np.zeros(nv, bool)
for s_ in 'LR':
    excl |= HAND[s_]
excl |= Wt[:, [gi[n] for n in names if n.startswith('B_Tail')]].sum(1) > 0.5
flag = skin & ~excl & (th < 0.035)
for _ in range(30):
    grow = flag.copy()
    for a_, b_ in ((0, 1), (1, 0)):
        m_ = flag[E[:, a_]] & ~flag[E[:, b_]] & (th[E[:, b_]] < 0.06) & ~excl[E[:, b_]]
        grow[E[m_, b_]] = True
    if (grow == flag).all():
        break
    flag = grow
lab = -np.ones(nv, np.int64); ncomp = 0
EF = E[flag[E[:, 0]] & flag[E[:, 1]]]
for sv in np.where(flag)[0]:
    if lab[sv] >= 0:
        continue
    lab[sv] = ncomp; stack = [sv]
    adj_ = EF[(EF[:, 0] == sv) | (EF[:, 1] == sv)]
    while stack:
        x = stack.pop()
        nb = np.concatenate([EF[EF[:, 0] == x, 1], EF[EF[:, 1] == x, 0]])
        for y in nb:
            if lab[y] < 0:
                lab[y] = ncomp; stack.append(y)
    ncomp += 1
nrig = 0
for c in range(ncomp):
    ids = np.where(lab == c)[0]
    ring = np.unique(np.concatenate([E[np.isin(E[:, 0], ids) & ~flag[E[:, 1]], 1], E[np.isin(E[:, 1], ids) & ~flag[E[:, 0]], 0]]))
    if len(ring) == 0 or len(ids) < 4:
        continue
    w = Wt[ring].mean(0); Wt[ids] = w / w.sum(); nrig += 1
print('RULE spikes rigid on their base:', nrig, 'spikes,', int(flag.sum()), 'vertices')
# head rigid above the neck joint (after the spike rule: the lips and the skull spikes are thin too and took the
# neck share of their base ring; the mouth's 2 mm edges then stretched 10x in the roar) (the skull, its spikes and ears), blended over the throat
hz = J('B_Head')[2]
ht_z = np.clip((co[:, 2] - (hz - 0.02)) / 0.06, 0, 1) * np.clip((-0.61 - co[:, 1]) / 0.02, 0, 1)   # not the back spikes
jaw = np.clip((-0.72 - co[:, 1]) / 0.03, 0, 1) * (co[:, 2] > 1.31)              # the jaw and lips hang below the atlas joint
ht = np.maximum(ht_z, jaw) * skin * (np.abs(co[:, 0]) < 0.20)                   # ear tips reach |x| 0.17
Wt *= (1 - ht)[:, None]; Wt[:, gi['B_Head']] += ht
print('RULE head: rigid', int((ht > 0.999).sum()), 'blended', int(((ht > 0) & (ht < 0.999)).sum()))
Wt[np.isin(gv, (1, 3))] = 0; Wt[np.isin(gv, (1, 3)), gi['B_Head']] = 1
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
