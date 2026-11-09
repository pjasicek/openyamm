"""Weights. Args: <heat npz (main hide, in its own index)> <out npz>. Main hide: mirrored heat, smoothed, fingers on their chains, tail on its bones; head by rules (helm rigid, neck band analytic, jaw by jawk, tongue chain); half joints; shells rigid or by the rules below."""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, 'scripts')
import rig_bones as RB, headfr as H
from rig_bones import half_pairs, FN, fk, TAIL, TONGUE
HEAT, OUT = sys.argv[1:3]
D = np.load('work/joined.npz'); co, tri, part, jk = D['co'].astype(float), D['tri'], D['part'], D['jawk']
nb = int(D['nb']); N = len(co)
H_ = np.load(HEAT); Wm = H_['W'].astype(np.float64); names = [str(x) for x in H_['names']]; mid = H_['ids'] if 'ids' in H_ else None
for n in ['Box01'] + TONGUE:
    if n not in names: names.append(n); Wm = np.c_[Wm, np.zeros(len(Wm))]
ix = {n: i for i, n in enumerate(names)}
main = np.where(part == 0)[0]
W = np.zeros((N, len(names))); W[main] = Wm
labels = np.zeros(N, int); lb = np.load('work/finger_labels.npy'); labels[:len(lb)] = lb
def swap(n): return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
perm = np.array([ix[swap(n)] for n in names])
d, m = cKDTree(co[main] * [-1, 1, 1]).query(co[main]); print('mirror max', d.max())
W[main] = .5 * (W[main] + W[main[m]][:, perm])
tm = tri[(part[tri] == 0).all(1)]
e = np.vstack([tm[:, [0, 1]], tm[:, [1, 2]], tm[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
fingers = labels > 0
free = (part == 0) & ~fingers
for it in range(int(os.environ.get('PASSES', '6'))):
    S_ = (A @ W) / deg[:, None]; W[free] = .5 * W[free] + .5 * S_[free]
P_, tips = RB.joints()
_ZS = [float(x) for x in os.environ.get('ZONESMOOTH', '.15,10,.22,40').split(',')]      # run 2: shoulder and hip zone smoothing (radius, passes)
for b, r, n_ in (('Bip01 L UpperArm', _ZS[0], int(_ZS[1])), ('Bip01 L Thigh', _ZS[2], int(_ZS[3]))):
    j = P_[b]; zone = (np.minimum(np.linalg.norm(co - j, axis=1), np.linalg.norm(co - j * [-1, 1, 1], axis=1)) < r) & free
    for it in range(n_):
        S_ = (A @ W) / deg[:, None]; W[zone] = .5 * W[zone] + .5 * S_[zone]
# fingers
for lab, f in enumerate(FN, 1):
    for s, sg in (('L', 1), ('R', -1)):
        vs = np.where((labels == lab) & (co[:, 0] * sg > 0))[0]
        allow = [ix[f'Bip01 {s} {fk(f, k)}'] for k in range(3)] + [ix[f'Bip01 {s} Hand']]
        mask = np.zeros(W.shape[1]); mask[allow] = 1; W[vs] *= mask
# palm: no arm or torso weights but Hand/Forearm
for s, sg in (('L', 1), ('R', -1)):
    wr = P_[f'Bip01 {s} Hand']; pm = (part == 0) & (labels == 0) & (co[:, 0] * sg > .5) & (co[:, 1] < .25)
    allow = np.zeros(W.shape[1]); allow[[ix[f'Bip01 {s} Hand'], ix[f'Bip01 {s} Forearm']] + [ix[f'Bip01 {s} {fk(f, 0)}'] for f in FN]] = 1; W[pm] *= allow
# tail: only tail bones and the pelvis
tv = (part == 0) & (np.abs(co[:, 0]) < .14) & (co[:, 2] < -.20) & (co[:, 1] < .10) & (co[:, 1] > -.5)
allow = np.zeros(W.shape[1]); allow[[ix[t] for t in TAIL] + [ix['Bip01 Pelvis']]] = 1; W[tv] *= allow
# feet and shins: no thigh leak below the calf's middle
# head
hd, nk, sp3, jw = ix['Bip01 Head'], ix['Bip01 Neck'], ix['Bip01 Spine3'], ix['Box01']
A0 = np.array([0, .735, .19]); B0 = np.array([0, .665, -.155]); uh = (A0 - B0) / np.linalg.norm(A0 - B0); nh_ = np.array([0, uh[2], -uh[1]])
if nh_[1] < 0: nh_ = -nh_
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
dh = (co - B0) @ nh_; dp = (co - H.PLANE_P) @ H.PLANE_N
NB = [float(x) for x in os.environ.get('NECKBAND', '-.30,.01,-.03,.06,-.12,.22').split(',')] + [-.075, .34]     # run 2: head ramp along the head axis, Spine3 ramp across the ring plane, body band start. r16 was -.13,-.012,-.03,.06,-.075; the wider ramps spread MM9's 85 deg head bend (Death) over the neck: neck faces failing collapse Death 164 -> 103
h = np.maximum(ss(dh, NB[0], NB[1]), ss(co[:, 2], .10, .20))
s3 = 1 - ss(dp, NB[2], NB[3])
An = np.zeros((N, W.shape[1])); An[:, hd] = h; An[:, sp3] = s3 * (1 - h); An[:, nk] = 1 - h - s3 * (1 - h)
rig = (part >= 1) & (part < 8)
W[part == 1] = An[part == 1]
# the body's band under the ring goes to the same function
band = (part == 0) & (dp > NB[4]) & (np.abs(co[:, 0]) < NB[5]) & (co[:, 1] > .45)
b = ss(dp[band], NB[4], -.002)[:, None]; W[band] = (1 - b) * W[band] + b * An[band]
sel = (part == 1) & (jk > 0); W[sel] = (1 - jk[sel, None]) * W[sel]; W[sel, jw] += jk[sel]
W[part == 3] = 0; W[part == 3, hd] = 1
W[part == 4] = 0; W[part == 4, jw] = 1
# tongue: along its chain
tp = np.array([P_[n] for n in TONGUE]); tv = part == 7; W[tv] = 0
for v in np.where(tv)[0]:
    t = np.clip((co[v] - tp[0]) @ (tp[-1] - tp[0]) / ((tp[-1] - tp[0]) @ (tp[-1] - tp[0])), 0, .999) * 3; i = int(t); f = t - i
    W[v, ix[TONGUE[i]]] += 1 - f; W[v, ix[TONGUE[i + 1]]] += f
# run 2: the armoured chest below the pecs carried 0.2-0.4 Clavicle and 0.1-0.25 upper arm weight down to y .25, and folded when the arm
# swung (Hit: 9 shoulder faces at x .11-.2, y .26-.41). There the arm side fades to Spine2, toward the chest's middle and bottom.
CH = float(os.environ.get('CHEST_ARM', 0))      # tried .8: Hit 9 -> 6 but AttackMelee 9 -> 15, Taunt 5 -> 10; off
if CH > 0:
    ax_ = np.abs(co[:, 0]); fz = CH * (1 - ss(ax_, .17, .25)) * (1 - ss(co[:, 1], .38, .50)) * ss(co[:, 1], .05, .15) * (part == 0) * ~fingers
    for s_ in 'LR':
        for b_ in ('Clavicle', 'UpperArm'):
            j_ = ix[f'Bip01 {s_} {b_}']; mv = W[:, j_] * fz; W[:, j_] -= mv; W[:, ix['Bip01 Spine2']] += mv
# half joints
pairs = half_pairs()
names = names + [h_ for h_, _, _, _ in pairs] + ['XFlap']
W = np.c_[W, np.zeros((N, len(pairs) + 1))]
ix = {n: i for i, n in enumerate(names)}
for h_, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a = W[:, ip].sum(1); b_ = W[:, ic]; m_ = np.minimum(a, b_)
    sel = (m_ > 1e-4) & ((part == 0) | ((part == 1) & (c in ('Box01', 'Bip01 Head', 'Bip01 Neck'))))
    W[sel, ix[h_]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
# shells (part = 8 + half comp, each once per side)
tmain = cKDTree(co[main])
def side(c): return np.where(c[:, 0] > 0, 'L', 'R')
PAUL = {16, 18, 19, 20, 21, 22, 24}
PLATE_TOP = int(os.environ.get('PLATE_TOP', 0))
for c in np.unique(part[part >= 8]):
    vs = np.where(part == c)[0]; W[vs] = 0; q = co[vs]; xc = q[:, 0]
    if c in PAUL:
        for v, s in zip(vs, side(q)): W[v, ix[f'Bip01 {s} XhalfUpperArm']] = 1
    elif c == 17:
        for v, s in zip(vs, side(q)): W[v, ix[f'Bip01 {s} Calf']] = 1
    elif c == 23:
        for v, s in zip(vs, side(q)): W[v, ix[f'Bip01 {s} Forearm']] = 1
    elif c in (14, 15):
        for v, s in zip(vs, side(q)):
            t = ss(-co[v, 1], -.085, -.03); W[v, ix['Bip01 Spine']] = 1 - t; W[v, ix[f'Bip01 {s} Thigh']] = t      # a hip plate is rigid on its thigh below a short band at the belt: it cannot pass through it
            if PLATE_TOP and t < 1:      # run 2: the band under the belt skirt takes the hide's own weights (the hide bulged over a Spine band when the thigh swung)
                W[v] = 0; W[v, ix[f'Bip01 {s} Thigh']] = t; W[v] += (1 - t) * W[main[tmain.query(co[v])[1]]]
    elif c == 9:
        for v in vs:
            t = ss(-co[v, 1], -.09, .03); W[v, ix['Bip01 Spine']] = 1 - t; W[v, ix['XFlap']] = t
    elif c in (10, 12):
        W[vs, ix['Bip01 Spine']] = 1
    elif c == 13:
        for v, s in zip(vs, side(q)):
            t = ss(-co[v, 1], -.09, -.01) * ss(abs(co[v, 0]), .06, .16) * .5; W[v, ix['Bip01 Spine']] = 1 - t; W[v, ix[f'Bip01 {s} XhalfThigh']] = t
    else:   # chest plate: the mean of what is under it, one rigid piece
        dd, mm = tmain.query(q); wm = W[main[mm]].mean(0); W[vs] = wm
# hide under the hip plates follows the plate (run 2): the plates are Spine at the belt and Thigh below, the hide under them was heat-weighted
# and bulged through their top and back edges when the thigh swung (Walking 1.7, AttackRanged 5.2 cm). Full within R0 of a plate point, none past R1.
R0, R1 = float(os.environ.get('PLATE_R0', .03)), float(os.environ.get('PLATE_R1', 0))
if R1 > 0:
    pv_ = np.where(np.isin(part, (14, 15)))[0]; tp_ = cKDTree(co[pv_])
    hv_ = np.where((part == 0) & ~fingers & (co[:, 1] < .12) & (co[:, 1] > -.24))[0]
    d_, k_ = tp_.query(co[hv_]); f_ = (1 - ss(d_, R0, R1))[:, None]
    W[hv_] = (1 - f_) * W[hv_] + f_ * W[pv_[k_]]
    print('hide under plates', int((f_ > .5).sum()), 'vertices')
# run 2, third request: the head ring takes its body copy's weights (it carried up to .34 jaw weight at the throat), so the neck-ring strip
# between them (folded, zero area at bind) never opens into the pale slivers seen in Hit2 and Dead; assemble.py also puts it on the copy
if os.environ.get('RINGWELD', '0') == '1':
    W[D['ringhead']] = W[D['ringcopy']]
if os.environ.get('INNERWELD', '0') == '1':      # tried: collapse Standing head 16 -> 33, Hit2 88 -> 108; off      # the head rim zipped to the ring copy (throat_paint.zipper) takes its nearest copy's weights, so the flat strip moves as one
    import throat_paint as _TP
    _st, _ = _TP.strip_and_chin(D); _rc = D['ringcopy']; _in = np.unique(_st[~np.isin(_st, _rc)])
    _nn = cKDTree(co[_rc]).query(co[_in])[1]; W[_in] = W[_rc[_nn]]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww[ww < .012] = 0; ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
print('max influences', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()))
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
