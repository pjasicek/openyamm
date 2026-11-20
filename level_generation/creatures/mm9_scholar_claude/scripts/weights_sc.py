"""Final weights for the Bembridge Scholar (SCHOLAR.abc Bip01 skeleton), after Igrid's weights_wo.py (the Wyrde's analytic route).
- ROBE and SKIRT below the waist: analytic over MM9's eight skirt chains (azimuth between two neighbouring chains, height between two
  neighbouring links of each: four influences, smooth), the waist band on XCOM_skirt; above the waist: spine heights, clavicles at the
  shoulders; sleeves by position along the arm (tight elbow), the cuff ring on the forearm.
- HOOD (the robe's shell above the jaw plane, near the head): rigid on Head, a band blending to Neck and Spine3 (the cowl round the neck).
- HEAD (face, eyes, circlet gem): rigid on Head above the jaw plane, a band to Neck, the lowest neck to Spine3.
- BRAIDS: on MM9's braid chains (xpony_a +x, xpony -x) by height, the top on Head.
- HANDS: MPFB weights onto our 15 finger bones. LEGS: Calf, Foot, Toe0. JEWEL: nearest robe / skirt / head weights.
Mirror symmetric. Half-joint helpers split elbow, shoulder, neck. Args: <asm npz> <mm9 npz> <rig json> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs, SKIRT_CHAINS, SKIRT_MIRROR
A_, M_, R_, OUT = sys.argv[1:5]
E = lambda k, d: float(os.environ.get(k, d))
D = np.load(A_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
M = np.load(M_); mjn = [str(x) for x in M['jn']]
Rj = json.load(open(R_)); JJ = Rj['joints']; MJ = {k: np.array(v) for k, v in Rj['mm9'].items()}
def J(n): return np.array(JJ[n]) if n in JJ else MJ[n]
names = list(mjn) + [f'Bip01 {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n] if n in pid else np.zeros(len(comp), bool)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
WAIST = float(os.environ.get('WAIST', '0.13'))
# ---- skirt chains by azimuth, links by height
CH = SKIRT_CHAINS
ang = np.array([np.arctan2(MJ[c[-1]][1], MJ[c[-1]][0]) for c in CH])
th = np.arctan2(co[:, 1], co[:, 0]); order = np.argsort(ang); angS = ang[order]
def link_w(chain, z):
    zs = np.array([MJ[b][2] for b in chain])
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
# ---- torso: spine heights (the stooped spine: height along the spine polyline), clavicles at the shoulders
Sb = ['Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck']; Zs = [MJ[b][2] for b in Sb]
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.09, 0.20) * ss(co[:, 2], MJ['Bip01 Spine3'][2] - 0.06, MJ['Bip01 Spine3'][2] + 0.04)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'Bip01 {s} Clavicle']] += k
for part in ('robe',):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.04)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
# ---- arms along the sleeve
sh = J('Bip01 R UpperArm'); el = J('Bip01 R Forearm'); wr = J('Bip01 R Hand'); ax = (wr - sh) / np.linalg.norm(wr - sh)
ELB = E('ELB', '0.06'); ARMR = E('ARMR', '0.17')
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = P('robe') & (co[:, 0] * sgn > 0.08) & (r < ARMR) & (t > -0.10)
    pre = f'Bip01 {s} '; Ua, Fa = ix[pre + 'UpperArm'], ix[pre + 'Forearm']
    rt = ss((co - e) @ a, -ELB, ELB)
    w_arm = np.zeros_like(W); w_arm[np.arange(len(co)), Ua] = 1 - rt; w_arm[np.arange(len(co)), Fa] = rt
    bl = ss(t, -0.03, 0.07) * (1 - ss(r, ARMR - 0.04, ARMR))
    W[arm] = W[arm] * (1 - bl[arm])[:, None] + w_arm[arm] * bl[arm][:, None]
# ---- smoothing on the bodice and the upper robe (the shoulder and waist blends), not on the skirt chains
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('robe') & (co[:, 2] > WAIST + 0.05), int(E('UP', '4')))
# ---- head: rigid above the jaw plane, a band to Neck / Spine3 below; cap rigid
JS, JZ, JY = E('JAW_SLOPE', '0.30'), E('JAW_Z', '0.70'), E('JAW_Y', '-0.08')
sj = co[:, 2] - JS * (co[:, 1] - JY) - JZ
zn = MJ['Bip01 Neck'][2]
hv = P('head'); W[hv] = 0; W[hv, ix['Bip01 Head']] = 1
u = ss(sj, -0.03, 0.01); lo = ss(co[:, 2], zn - 0.01, zn + 0.05); neck = hv & (sj < 0.01)
W[neck] = 0; W[neck, ix['Bip01 Head']] = u[neck]; W[neck, ix['Bip01 Neck']] = ((1 - u) * lo)[neck]; W[neck, ix['Bip01 Spine3']] = ((1 - u) * (1 - lo))[neck]
cp = P('cap'); W[cp] = 0; W[cp, ix['Bip01 Head']] = 1
# ---- hair and beard: the beard (in front, below the chin) on Ybeardpiv -> Ybeard by height; the side locks on Yhair chains; the rest of
# the hair on Head, its lowest back part blending to Neck / Spine3
hr = P('hair'); W[hr] = 0
bp, bt_ = MJ['Ybeardpiv'], MJ['Ybeard']
front = ss(-co[:, 1], 0.03, 0.08)            # in front of the face plane
zb = co[:, 2]; tb = np.clip((bp[2] + 0.03 - zb) / (bp[2] + 0.03 - bt_[2]), 0, 1.4)
wb = front * ss(bp[2] + 0.03 - zb, 0.0, 0.04)
q = np.where(hr)[0]
W[q, ix['Bip01 Head']] = 1 - wb[q]
W[q, ix['Ybeardpiv']] += wb[q] * np.clip(1 - tb[q], 0, 1); W[q, ix['Ybeard']] += wb[q] * np.clip(tb[q], 0, 1)
for side, sx in (('', -1), ('01', 1)):
    hp_, ht2 = MJ['Yhairpiv' + side], MJ['Yhair' + side]
    sidew = (1 - front) * ss(co[:, 0] * sx, 0.06, 0.11) * ss(hp_[2] - zb, 0.0, 0.06) * (co[:, 1] < 0.06)
    th2 = np.clip((hp_[2] - zb) / (hp_[2] - ht2[2]), 0, 1)
    k = sidew[q]; W[q] *= (1 - k)[:, None]; W[q, ix['Yhairpiv' + side]] += k * (1 - th2[q]); W[q, ix['Yhair' + side]] += k * th2[q]
backw = (1 - front) * ss(zn + 0.03 - zb, 0.0, 0.08) * (co[:, 1] > 0.0)
k = backw[q]; lo2 = ss(zb, zn - 0.06, zn)[q]
W[q] *= (1 - k)[:, None]; W[q, ix['Bip01 Neck']] += k * lo2; W[q, ix['Bip01 Spine3']] += k * (1 - lo2)
print('HAIR verts', int(hr.sum()), 'beard', int((wb[q] > 0.5).sum()))
# ---- jewellery: the nearest robe / skirt / head weights, smoothed per piece
if P('jewel').any():
    # robe only: beads near the beard took Head weights and lifted off the stole (detached audit)
    src = np.where(P('robe'))[0]; kd = cKDTree(co[src]); q = np.where(P('jewel'))[0]
    W[q] = W[src[kd.query(co[q])[1]]]; smooth(P('jewel'), 4)
# ---- hands: MPFB weights by position
hc, hW, hb = D['hand_co'], D['hand_W'], [str(x) for x in D['hand_bones']]
hk = cKDTree(np.vstack([hc, hc * [-1, 1, 1]]))
_, nv = hk.query(co[P('hands')]); side = nv >= len(hc); nv = nv % len(hc); hv2 = np.where(P('hands'))[0]
HM = {}
for f, nm in enumerate(FINGERS, 1):
    for k in (1, 2, 3): HM[f'finger{f}-{k}'] = nm + str(k)
for i, v in enumerate(hv2):
    s = 'L' if side[i] else 'R'; pre = f'Bip01 {s} '
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
    pre = f'Bip01 {s} '; side = co[:, 0] * sgn > 0
    toe = MJ[pre + 'Toe0']; foot = MJ[pre + 'Foot']
    lv = P('legs') & side; W[lv] = 0
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.05); cw = ss(co[:, 2], foot[2] + 0.02, foot[2] + 0.08)
    W[lv, ix[pre + 'Toe0']] = (tw * (1 - cw))[lv]; W[lv, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[lv]; W[lv, ix[pre + 'Calf']] = cw[lv]
# ---- symmetric
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix[swap(n)] for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co)
for part in ('robe', 'head', 'hair'):
    q = P(part); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
print('mirror max', round(float(d[P('robe')].max()), 5))
# ---- coincident vertices across part seams take one averaged weight set
_key = np.round(co, 5); _u, _inv = np.unique(_key, axis=0, return_inverse=True); _inv = _inv.ravel()
_cnt = np.bincount(_inv); _multi = _cnt[_inv] > 1
_acc = np.zeros((len(_u), W.shape[1])); np.add.at(_acc, _inv, W); _avg = _acc / _cnt[:, None]
W[_multi] = _avg[_inv[_multi]]; print('SEAM welded vertices', int(_multi.sum()))
# ---- half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('legs')
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
