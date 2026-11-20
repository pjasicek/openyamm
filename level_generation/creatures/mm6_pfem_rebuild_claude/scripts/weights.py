"""Weights for the MM6 PeasantF1 rebuild on MM9's PeasantFemale skeleton (after mm9_peasantf1_claude/scripts/weights_pf.py).
- skirt + lining: analytic over MM9's eight skirt chains (azimuth between two neighbouring chains, height between two neighbouring links),
  blended into the torso at the waist;
- dress (bodice, chest, neck, short sleeves): spine bands by height, clavicles at the shoulders, the sleeves by position along the arm;
- neck and face: a slanted jaw plane (under the chin low, the skull base high): above it rigid Head, a band to Neck, the neck base Spine3;
- hair, circlet: Head; braid: Head at its root, then Ponytail11 -> Ponytail12 down the plait;
- hands (MPFB arm + hand): MPFB's own weights mapped to our bones (upper arm, forearm, hand, 15 finger bones);
- legs: Calf, Foot, Toe0; belt: the nearest bodice/skirt weights, smoothed; buckle: the belt's mean;
- mirror-symmetric, half-joint helpers at shoulders, elbows and neck, 4 influences.
Args: <asm npz> <rig json> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs, SKIRT_CHAINS, SKIRT_MIRROR
A_, R_, OUT = sys.argv[1:4]
D = np.load(A_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
Rj = json.load(open(R_)); JJ = {k: np.array(v) for k, v in Rj['joints'].items()}
MJ = {k: np.array(v) for k, v in Rj['mm9'].items()}
mjn = [n for n in MJ if not n.endswith('.mesh') and n not in ('NGon01', 'F1a', 'Scene Root')]
J = lambda n: JJ[n]
names = list(mjn) + [f'FHP {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n] if n in pid else np.zeros(len(comp), bool)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
WAIST = Rj['waist']; CY = Rj['skirt_cy']
# ---- skirt: chains by azimuth, links by height
CH = SKIRT_CHAINS
ang = np.array([np.arctan2(J(c[-1])[1] - CY, J(c[-1])[0]) for c in CH])
th = np.arctan2(co[:, 1] - CY, co[:, 0]); order = np.argsort(ang); angS = ang[order]
def link_w(chain, z):
    zs = np.array([J(b)[2] for b in chain])
    i = np.clip(np.searchsorted(-zs, -z, side='right') - 1, 0, len(zs) - 2)
    t = np.clip((zs[i] - z) / np.maximum(zs[i] - zs[i + 1], 1e-4), 0, 1)
    return i, t
Wa = np.zeros((len(co), len(names))); gap = np.diff(np.r_[angS, angS[0] + 2 * np.pi])
for k in range(len(angS)):
    a0, g0 = angS[k], gap[k]; d0 = (th - a0) % (2 * np.pi); sel = np.where(d0 < g0)[0]
    u = d0[sel] / g0; u = u * u * (3 - 2 * u); c0, c1 = CH[order[k]], CH[order[(k + 1) % len(angS)]]
    for ch, wt in ((c0, 1 - u), (c1, u)):
        i, t = link_w(ch, co[sel, 2]); bi = np.array([ix[b] for b in ch])
        np.add.at(Wa, (sel, bi[i]), wt * (1 - t)); np.add.at(Wa, (sel, bi[i + 1]), wt * t)
# ---- torso: spine heights, the pelvis below the waist
Sb = ['XCOM_skirt', 'FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck']; Zs = [J(b)[2] for b in Sb]; Zs[0] = WAIST - 0.03
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.07, 0.15) * ss(co[:, 2], J('FHP Spine3')[2] - 0.04, J('FHP Spine3')[2] + 0.05)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'FHP {s} Clavicle']] += k
for part in ('skirt', 'lining'):
    q = P(part); k = ss(co[:, 2], WAIST - 0.06, WAIST - 0.005)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
W[P('dress')] = Wt[P('dress')]          # the bodice never follows the skirt chains (MM9's stand flares them at the waist: a peplum)
# ---- arms along the sleeve
sh = J('FHP R UpperArm'); el = J('FHP R Forearm'); wr = J('FHP R Hand'); ax = (wr - sh) / np.linalg.norm(wr - sh)
ELB = float(os.environ.get('ELB', '0.06'))
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = P('dress') & (co[:, 0] * sgn > 0.08) & (r < float(os.environ.get('ARMR', '0.085'))) & (t > -0.10) & (co[:, 2] > sh[2] - 0.11)
    pre = f'FHP {s} '; Ua, Fa = ix[pre + 'UpperArm'], ix[pre + 'Forearm']
    rt = ss((co - e) @ a, -ELB, ELB)
    w_arm = np.zeros_like(W); w_arm[np.arange(len(co)), Ua] = 1 - rt; w_arm[np.arange(len(co)), Fa] = rt
    bl = ss(t, -0.03, 0.07)
    W[arm] = W[arm] * (1 - bl[arm])[:, None] + w_arm[arm] * bl[arm][:, None]
# ---- smoothing on the bodice (the shoulder and waist blends)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('dress') & (co[:, 2] > WAIST + 0.05) & (co[:, 2] < J('FHP Neck')[2] - 0.01), int(os.environ.get('UP', '4')))
# ---- neck and face: the slanted jaw plane
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
zn = J('FHP Neck')[2]; HD = J('FHP Head')
CHIN_Y, CHIN_Z, SLOPE = float(os.environ.get('CHIN_Y', '-0.07')), float(os.environ.get('CHIN_Z', '0.555')), 0.30
sj = co[:, 2] - SLOPE * (co[:, 1] - CHIN_Y) - CHIN_Z
u = ss(sj, -0.025, 0.01); lo = ss(co[:, 2], zn + 0.01, zn + 0.06)
hn = (P('head') | P('dress')) & (co[:, 2] > zn - 0.005) & (np.abs(co[:, 0]) < 0.075)
W[hn] = 0; W[hn, ix['FHP Head']] = u[hn]; W[hn, ix['FHP Neck']] = ((1 - u) * lo)[hn]; W[hn, ix['FHP Spine3']] = ((1 - u) * (1 - lo))[hn]
rigid(P('head') & ~hn, 'FHP Head')
smooth(hn & ~P('head') | (P('head') & (sj < 0.02)), 2, 0.4)
rigid(P('hair') | P('band'), 'FHP Head')
# braid: Head at the root, Ponytail11 to Ponytail12 down the plait
bv = P('braid'); p11, p12 = J('FHP Ponytail11'), J('FHP Ponytail12')
zb = co[:, 2]; wroot = ss(zb, p11[2] - 0.02, p11[2] + 0.02)
w12 = ss(zb, p11[2] - 0.01, p12[2] - 0.02) if p12[2] > p11[2] else 1 - ss(zb, p12[2] - 0.0, p11[2] - 0.0)
W[bv] = 0; W[bv, ix['FHP Head']] = wroot[bv]; W[bv, ix['FHP Ponytail11']] = ((1 - wroot) * (1 - w12))[bv]; W[bv, ix['FHP Ponytail12']] = ((1 - wroot) * w12)[bv]
# ---- hands: MPFB weights by position
hc, hW, hb = D['hand_co'], D['hand_W'], [str(x) for x in D['hand_bones']]
hk = cKDTree(np.vstack([hc, hc * [-1, 1, 1]]))
_, nv = hk.query(co[P('hands')]); side = nv >= len(hc); nv = nv % len(hc); hv2 = np.where(P('hands'))[0]
HM = {}
for f, nm in enumerate(FINGERS, 1):
    for k in (1, 2, 3): HM[f'finger{f}-{k}'] = nm + str(k)
for i, v in enumerate(hv2):
    s = 'L' if side[i] else 'R'; pre = f'FHP {s} '
    W[v] = 0
    for b, wt in zip(hb, hW[nv[i]]):
        if wt < 1e-3: continue
        b0 = b.split('.')[0]
        if b0 in HM: W[v, ix[pre + HM[b0]]] += wt
        elif b0 in ('wrist',) or b0.startswith('metacarpal'): W[v, ix[pre + 'Hand']] += wt
        elif b0.startswith('upperarm'): W[v, ix[pre + 'UpperArm']] += wt
        else: W[v, ix[pre + 'Forearm']] += wt
    if W[v].sum() < 1e-6: W[v, ix[pre + 'Forearm']] = 1
# ---- legs: toe forward of the ball, foot, calf above the ankle
for s, sgn in (('R', 1), ('L', -1)):
    pre = f'FHP {s} '; side = co[:, 0] * sgn > 0
    toe = J(pre + 'Toe0'); foot = J(pre + 'Foot')
    lv = P('legs') & side; W[lv] = 0
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.05); cw = ss(co[:, 2], foot[2] + 0.02, foot[2] + 0.08)
    W[lv, ix[pre + 'Toe0']] = (tw * (1 - cw))[lv]; W[lv, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[lv]; W[lv, ix[pre + 'Calf']] = cw[lv]
# ---- belt: nearest bodice/skirt weights, smoothed; buckle: the belt's weights at its centre
q = np.where(P('belt'))[0]; W[q] = Wt[q]                 # the belt rides with the bodice (torso bands), so no gap opens between them
bq = np.where(P('buckle'))[0]; kb = cKDTree(co[q]); W[bq] = W[q[kb.query(co[bq], k=6)[1]]].mean(1).mean(0)[None]
# ---- symmetric
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix[swap(n)] for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co)
for part in ('skirt', 'lining', 'dress', 'belt', 'head', 'hair', 'band'):
    q = P(part) & (d < 0.002); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
# ---- coincident vertices across part seams take one averaged weight set
_key = np.round(co, 5); _u, _inv = np.unique(_key, axis=0, return_inverse=True); _inv = _inv.ravel()
_cnt = np.bincount(_inv); _multi = _cnt[_inv] > 1
_acc = np.zeros((len(_u), W.shape[1])); np.add.at(_acc, _inv, W); _avg = _acc / _cnt[:, None]
W[_multi] = _avg[_inv[_multi]]; print('SEAM welded vertices', int(_multi.sum()))
# ---- half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('legs') | P('hair') | P('band')
for h, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
    sel = (m_ > 1e-4) & ~rigidp
    W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww = np.where(ww < 0.012, 0, ww); ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
lost = 1 - np.take_along_axis(W, ord_, 1).sum(1) / np.maximum(W.sum(1), 1e-9)
print('WEIGHTS influences', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()), 'cut to 4: max lost', round(float(lost.max()), 3),
      {pn[k]: int((W[comp == k].sum(1) < 1e-5).sum()) for k in range(len(pn)) if (W[comp == k].sum(1) < 1e-5).any()})
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
