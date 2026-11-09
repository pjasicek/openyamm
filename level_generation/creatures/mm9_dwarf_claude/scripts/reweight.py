"""Weights on the frozen mesh (UVs and paints stay): where the collapse gate found folds. Knee pivot further toward the back of the leg, ankle half-joint helpers Foot_h, relax on the neck band, shoulders and armpits, elbows, knee backs. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
B = 'Bip01 '
ELBOW = 0.0
KNEE = float(sys.argv[sys.argv.index('--') + 3]) if len(sys.argv) > sys.argv.index('--') + 3 else 0.02
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted().to_3x3()
for s in 'LR':
    e = eb[f'{B}{s} Calf']; v = Mi @ Vector((0, KNEE, 0)); e.head += v; e.tail += v
    h = eb[f'{B}{s} Calf_h']; h.head += v; h.tail += v
    e = eb[f'{B}{s} Forearm']; v = Mi @ Vector((0, ELBOW, 0)); e.head += v; e.tail += v
    h = eb[f'{B}{s} Forearm_h']; h.head += v; h.tail += v
    f = eb[f'{B}{s} Foot']; n = eb.new(f'{B}{s} Foot_h'); n.head = f.head; n.tail = f.tail; n.roll = f.roll; n.parent = f.parent; n.use_connect = False
# run 2: the skirt's leg share follows the thigh on its own bones, pivoting on the cloth at the belt (front and back hinge line), not about the hip:
# a share on the thigh itself turned about the hip pushed the cloth at hip height up under the belt (the shiny roll in Running and AttackMelee).
# SkirtLegF_* follow the thigh's forward swing only, SkirtLegB_* its backward swing (skirt_leg_keys.py): a back panel is not pulled into the seat.
Mw = rig.matrix_world; Mwi = Mw.inverted()
hw = {k: Mw @ eb[k].head for k in ('Skirt_FR', 'Skirt_FL', 'Skirt_BR', 'Skirt_BL', 'Skirt_SFL', 'Skirt_SFR')}
HZ_ = sum(hw[k].z for k in hw) / len(hw); YF_ = 0.5 * (hw['Skirt_FR'].y + hw['Skirt_FL'].y); YB_ = 0.5 * (hw['Skirt_BR'].y + hw['Skirt_BL'].y)
XS_ = 0.5 * (abs(hw['Skirt_SFL'].x) + abs(hw['Skirt_SFR'].x))
spb = eb[B + 'Spine']; Rt_ = spb.matrix.to_3x3()
for s in 'LR':
    sg_ = 1 if s == 'L' else -1
    for fb, yy in (('F', YF_), ('B', YB_)):
        n = eb.new(f'SkirtLeg{fb}_{s}'); hp = Mwi @ Vector((sg_ * XS_, yy, HZ_))
        n.head = hp; n.tail = hp + Rt_.col[1] * 0.08; n.align_roll(Rt_.col[2]); n.parent = spb; n.use_connect = False; n.use_deform = True
print('SKIRTLEG pivots z', round(HZ_, 3), 'front y', round(YF_, 3), 'back y', round(YB_, 3), 'side x', round(XS_, 3))
bpy.ops.object.mode_set(mode='OBJECT')
n = len(me.vertices); P = np.array([v.co[:] for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
for s in 'LR': body.vertex_groups.new(name=f'{B}{s} Foot_h')
for s in 'LR':
    for fb in 'FB': body.vertex_groups.new(name=f'SkirtLeg{fb}_{s}')
names = [g.name for g in body.vertex_groups]; idx = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
skin = np.isin(pa, (1, 5, 6))
def bump_(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def relax(mask, its, k=0.5):
    ids = np.nonzero(mask & skin)[0]
    for _ in range(its):
        W[ids] = (1 - k) * W[ids] + k * np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
    print('RELAX', len(ids), its)
# ankle helpers: the boot's band between calf and foot
for s in 'LR':
    c, f, h = idx[f'{B}{s} Calf'], idx[f'{B}{s} Foot'], idx[f'{B}{s} Foot_h']
    ch = idx.get(f'{B}{s} Calf_h')
    wc = W[:, c]; wf = W[:, f]; tot = wc + wf; m = (wc > 1e-3) & (wf > 1e-3) & (pa == 6)
    t = wf[m] / tot[m]
    W[m, c] = tot[m] * np.maximum(1 - 2 * t, 0); W[m, f] = tot[m] * np.maximum(2 * t - 1, 0); W[m, h] = tot[m] * (1 - np.abs(2 * t - 1))
    print('FOOT_H', s, int(m.sum()))
for s in 'LR':
    relax((np.linalg.norm(P - J[f'{B}{s} UpperArm'], axis=1) < 0.17) & (pa == 1), 10)
    relax((np.linalg.norm(P - J[f'{B}{s} Forearm'], axis=1) < 0.13) & (pa == 1), 9)
    relax((np.linalg.norm(P - J[f'{B}{s} Calf'], axis=1) < 0.11) & (pa == 5), 4)
    relax((np.linalg.norm(P - J[f'{B}{s} Foot'], axis=1) < 0.13) & (pa == 6), 8)
# the skirt's hem a little narrower: MM9's hand swings past it
q = np.nonzero(pa == 7)[0]
P[q, 0] *= 1 - 0.07 * (1 - bump_(P[q, 2], -0.22, -0.10))
for i_ in q: me.vertices[int(i_)].co = Vector(P[i_])
# the face and the whole beard are rigid on the head (user: a tip held by the chest stretched in the attacks)
q = np.nonzero(pa == 20)[0]
W[q] = 0; W[q, idx[B + 'Head']] = 1.0
# the shoulders under the helmet's rim: more room for a head tipped back
RIM = 0.33; cy_ = -0.01
q = np.nonzero(pa == 1)[0]
r_ = np.hypot(P[q, 0], (P[q, 1] - cy_) * 0.85)
lim = RIM - 0.035 + np.maximum(r_ - 0.125, 0) * 1.2
k_ = 1 - bump_(r_, 0.16, 0.22)
hit = (P[q, 2] > lim) & (r_ < 0.22)
P[q[hit], 2] = P[q[hit], 2] * (1 - k_[hit]) + lim[hit] * k_[hit]
for i_ in q[hit]: me.vertices[int(i_)].co = Vector(P[i_])
print('SKIRT dome', int(hit.sum()))
# run 2: the skin under the helmet's rim goes with the head by a share (HEAD_SHARE at the rim, fading over 9 cm down and outward past r 0.17): a head tipped
# back or nodded presses the rim and the beard into the shoulders and the chest, so the skin there gives way as a neck's would. Plates half as much.
HS = float(__import__('os').environ.get('HEAD_SHARE', 0.4))
armw_ = W[:, [idx[f'{B}{s_} {b_}'] for s_ in 'LR' for b_ in ('UpperArm', 'Forearm', 'UpperArm_h', 'Forearm_h') if f'{B}{s_} {b_}' in idx]].sum(1)
q = np.nonzero(np.isin(pa, (1, 12)) & (armw_ < 0.3))[0]
r_ = np.hypot(P[q, 0], (P[q, 1] - cy_) * 0.85)
lim = RIM - 0.035 + np.maximum(r_ - 0.125, 0) * 1.2
t_ = HS * bump_(P[q, 2], lim - 0.09, lim - 0.01) * (1 - bump_(r_, 0.17, 0.25)) * (1 - armw_[q] / 0.3) * np.where(pa[q] == 12, 0.5, 1.0)
W[q] *= (1 - t_)[:, None]; W[q, idx[B + 'Head']] += t_
print('HEAD share', int((t_ > 0.01).sum()), 'verts, max', round(float(t_.max()), 2))
# the neck tube: a long band, the head nods over the whole tube
q = np.nonzero(pa == 24)[0]
hb, nb_i = idx[B + 'Head'], idx[B + 'Neck']
hh_ = np.clip((P[q, 2] - 0.29) / 0.15, 0, 1); hh_ = hh_ * hh_ * (3 - 2 * hh_)
W[q] = 0; W[q, hb] = hh_; W[q, nb_i] = 1 - hh_
# skirt: the hinges take over right under the belt, or the thigh comes through the top of the cloth
sk = [idx[k] for k in names if k.startswith('Skirt_')]; sp = idx[B + 'Spine']
q = np.nonzero(pa == 7)[0]
tot = W[q][:, sk].sum(1); rn = np.clip((float(__import__('os').environ.get('SK_TOP', -0.012)) - P[q, 2]) / float(__import__('os').environ.get('SK_BAND', 0.05)), 0, 1); rn = rn * rn * (3 - 2 * rn)
pat = np.zeros((len(q), len(sk))); pat[tot > 1e-6] = W[q][tot > 1e-6][:, sk] / tot[tot > 1e-6, None]
nb_ = np.nonzero(tot <= 1e-6)[0]
if len(nb_):                                      # the top ring had no hinge share: take the nearest vertex's pattern
    have = np.nonzero(tot > 1e-6)[0]
    for i_ in nb_: pat[i_] = pat[have[np.argmin(np.linalg.norm(P[q[have]] - P[q[i_]], axis=1))]]
for k, j in enumerate(sk): W[q, j] = pat[:, k] * rn
W[q, sp] = 1 - rn
# the skirt hangs and goes with the legs (user, Clan Soldier): toward the hem part of each vertex follows the thigh on its side, so a hinge only lifts what a thigh still reaches
KK = [float(x) for x in __import__('os').environ.get('KK', '0.72,-0.03,0.16,0.65').split(',')]   # run 2 (leg bones pivot at the belt): the share starts higher, so the cloth over the thigh's top goes with it
kk = KK[0] * np.clip((KK[1] - P[q, 2]) / KK[2], 0, 1) ** KK[3]
sL = np.clip((P[q, 0] + 0.11) / 0.22, 0, 1); sL = sL * sL * (3 - 2 * sL)
W[q] *= (1 - kk)[:, None]
yT = 0.5 * (J[B + 'L Thigh'][1] + J[B + 'R Thigh'][1])               # front is -y: split the leg share front/back across the hip line
fF = np.clip((yT + float(__import__('os').environ.get('FB_BAND', 0.05)) - P[q, 1]) / (2 * float(__import__('os').environ.get('FB_BAND', 0.05))), 0, 1); fF = fF * fF * (3 - 2 * fF)
W[q, idx['SkirtLegF_L']] += kk * sL * fF; W[q, idx['SkirtLegB_L']] += kk * sL * (1 - fF)
W[q, idx['SkirtLegF_R']] += kk * (1 - sL) * fF; W[q, idx['SkirtLegB_R']] += kk * (1 - sL) * (1 - fF)
print('SKIRT band', len(q), float(rn.min()), float(rn.max()))
# the thigh under the skirt: Meshy's pants are as deep as the cloth, so a swinging leg comes through the tunic. Slimmed toward the leg's axis where the skirt hides it, fading out above the hem
TOP, LOW, K = -0.05, -0.31, float(__import__('os').environ.get('THIGH_K', 0.55))
for s_ in 'LR':
    a = J[f'{B}{s_} Thigh']; b = J[f'{B}{s_} Calf']; u = (b - a) / np.linalg.norm(b - a)
    sg = 1 if s_ == 'L' else -1
    q = np.nonzero((pa == 5) & (P[:, 0] * sg > 0))[0]
    v = P[q] - a; al = v @ u; rad = v - np.outer(al, u)
    k = np.clip((P[q, 2] - LOW) / 0.05, 0, 1); k = k * k * (3 - 2 * k)
    f = 1 - (1 - K) * k
    # run 2: the hip's outer side under the upper skirt, a little further in (a thigh swung up met the cloth under the belt at the side, AttackMelee2, Death2)
    KO = float(__import__('os').environ.get('THIGH_OUT', 0.55))
    k2 = np.clip((P[q, 2] - float(__import__('os').environ.get('THIGH_OUT_Z', -0.26))) / 0.06, 0, 1); k2 = k2 * k2 * (3 - 2 * k2)
    outw = np.clip(sg * rad[:, 0] / 0.02, 0, 1)
    fo = 1 - (1 - KO) * k2 * outw
    rad = rad * f[:, None]; rad[:, 0] *= fo
    P[q] = a + np.outer(al, u) + rad
    for i_ in q: me.vertices[int(i_)].co = Vector(P[i_])
print('SKIRT thighs slimmed', K, 'hip side', KO)
# the belly: Meshy's chest stands 6 cm further forward than MM9's, and MM9's hand-on-hip and folded-arm clips run into it. Vertices only: UVs and paint stay
FB = float(__import__('os').environ.get('BELLY', 0.72))
q = np.nonzero(np.isin(pa, (1, 12)))[0]
wz = bump_(P[q, 2], -0.04, 0.07) * (1 - bump_(P[q, 2], 0.22, 0.34)); wx = 1 - bump_(np.abs(P[q, 0]), 0.19, 0.26)
fr = P[q, 1] < 0.0
f = 1 - (1 - FB) * wz * wx
P[q[fr], 1] = P[q[fr], 1] * f[fr]
for i_ in q: me.vertices[int(i_)].co = Vector(P[i_])
# the waist: MM9's fist on the hip goes into Meshy's wider flank. Tunic, belt and the skirt's top, not the arms
FW = float(__import__('os').environ.get('WAIST', 0.80))
armw = W[:, [idx[f'{B}{s_} {b_}'] for s_ in 'LR' for b_ in ('UpperArm', 'Forearm', 'UpperArm_h', 'Forearm_h') if f'{B}{s_} {b_}' in idx]].sum(1)
q = np.nonzero(np.isin(pa, (1, 7, 9)) & (armw < 0.3))[0]
wz = np.where(pa[q] == 7, bump_(P[q, 2], -0.08, -0.03), bump_(P[q, 2], -0.14, -0.03)) * (1 - bump_(P[q, 2], 0.12, 0.22))
P[q, 0] *= 1 - (1 - FW) * wz
for i_ in q: me.vertices[int(i_)].co = Vector(P[i_])
me.update()
# run 2 (coordinator): the glove opened from the bracer when the wrist bent hard - a dark wedge of the bracer's cap between them. The glove's hand share
# jumped 0 -> 0.8 within 1 cm at the cuff and the bracer was rigid on the forearm. Now the glove's share rises smoothly from inside the cuff (GLOVE_A..B
# along the forearm from the wrist) and the bracer's last centimetres take up to CUFF_SHARE of the hand, so the cuff's mouth leans with the wrist.
import os as _os
hfl = np.zeros(len(me.polygons), int)
if 'hand' in me.attributes: me.attributes['hand'].data.foreach_get('value', hfl)
hv_ = np.zeros(n, bool)
for p_ in me.polygons:
    if hfl[p_.index]:
        for v_ in p_.vertices: hv_[v_] = True
GA, GB = float(_os.environ.get('GLOVE_A', -0.035)), float(_os.environ.get('GLOVE_B', 0.03))
CS, CA, CB = float(_os.environ.get('CUFF_SHARE', 0.45)), float(_os.environ.get('CUFF_A', -0.035)), float(_os.environ.get('CUFF_B', 0.008))
for s_ in 'LR':
    Hj, Fj = J[f'{B}{s_} Hand'], J[f'{B}{s_} Forearm']; u_ = (Hj - Fj) / np.linalg.norm(Hj - Fj)
    al_ = (P - Hj) @ u_; rad_ = np.linalg.norm((P - Hj) - np.outer(al_, u_), axis=1)
    side_ = np.sign(P[:, 0]) == (1 if s_ == 'L' else -1)
    hb_ = [idx[k] for k in names if k.startswith(f'{B}{s_} ') and any(t in k for t in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Finger'))]
    fa_ = [idx[k] for k in (f'{B}{s_} Forearm', f'{B}{s_} Forearm_h') if k in idx]
    hand_i = idx[f'{B}{s_} Hand']
    # the glove: a smooth share across the seam, only where it was below the new curve (fingers and palm keep theirs)
    q_ = np.nonzero(hv_ & side_ & (al_ > GA - 0.01) & (al_ < GB) & (rad_ < 0.09))[0]
    tgt = bump_(al_[q_], GA, GB)
    cur = W[q_][:, hb_].sum(1)
    for i_, t_, c_ in zip(q_, tgt, cur):
        if abs(t_ - c_) < 1e-4: continue
        rest_ = W[i_].copy(); rest_[hb_] = 0; rs = rest_.sum()
        if c_ > 1e-6: W[i_, hb_] *= t_ / c_
        else: W[i_, hand_i] = t_
        if rs > 1e-9: W[i_] = np.where(np.isin(np.arange(len(names)), hb_), W[i_], rest_ * (1 - t_) / rs)
    # the bracer's mouth
    q2 = np.nonzero(~hv_ & side_ & (pa == 1) & (al_ > CA) & (rad_ < 0.09))[0]
    t2 = CS * bump_(al_[q2], CA, CB)
    W[q2] *= (1 - t2)[:, None]; W[q2, hand_i] += t2
    print('WRIST', s_, 'glove verts', len(q_), 'cuff verts', len(q2), 'cuff share max', round(float(t2.max()) if len(t2) else 0, 2))
order = np.argsort(-W, axis=1)
for i in np.nonzero(skin | (pa == 7) | (pa == 24) | (pa == 20))[0]:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for g in body.vertex_groups:
    j = g.index
    g.remove(list(range(n)))
    for i in np.nonzero(W[:, j])[0]: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('REWEIGHT done')
