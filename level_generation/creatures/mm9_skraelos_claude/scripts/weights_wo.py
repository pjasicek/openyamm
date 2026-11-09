"""Final weights for Igrid (wyrd_old's stooped human female skeleton), after the Wyrde's weights_wy.py.
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
names = list(mjn) + [f'FHP {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n] if n in pid else np.zeros(len(comp), bool)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
WAIST = MJ['XCOM_skirt'][2]
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
Sb = ['XCOM_skirt', 'FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck']; Zs = [MJ[b][2] for b in Sb]; Zs[0] = WAIST - 0.03
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.06, 0.14) * ss(co[:, 2], MJ['FHP Spine3'][2] - 0.04, MJ['FHP Spine3'][2] + 0.05)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'FHP {s} Clavicle']] += k
for part in ('robe', 'skirt'):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
# ---- arms along the sleeve
sh = J('FHP R UpperArm'); el = J('FHP R Forearm'); wr = J('FHP R Hand'); ax = (wr - sh) / np.linalg.norm(wr - sh)
ELB = E('ELB', '0.06'); ARMR = E('ARMR', '0.17')
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = P('robe') & (co[:, 0] * sgn > 0.08) & (r < ARMR) & (t > -0.10)
    pre = f'FHP {s} '; Ua, Fa = ix[pre + 'UpperArm'], ix[pre + 'Forearm']
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
# ---- the jaw plane (under the chin at the front, rising toward the skull base behind)
JS, JZ, JY = E('JAW_SLOPE', '0.30'), E('JAW_Z', '0.445'), E('JAW_Y', '-0.28')
sj = co[:, 2] - JS * (co[:, 1] - JY) - JZ
zn = MJ['FHP Neck'][2]
def headblend(mask, lo, hi):
    u = ss(sj, lo, hi); low = ss(co[:, 2], zn - 0.02, zn + 0.04)
    W[mask] = W[mask] * (1 - u[mask])[:, None]
    W[mask, ix['FHP Head']] += u[mask]
    return u
hv = P('head'); W[hv] = 0; W[hv, ix['FHP Head']] = 1
u = ss(sj, -0.03, 0.01); lo = ss(co[:, 2], zn - 0.01, zn + 0.05); neck = hv & (sj < 0.01)
W[neck] = 0; W[neck, ix['FHP Head']] = u[neck]; W[neck, ix['FHP Neck']] = ((1 - u) * lo)[neck]; W[neck, ix['FHP Spine3']] = ((1 - u) * (1 - lo))[neck]
# hood: the robe's shell near the head and above the jaw plane follows the head; the band below to Neck / Spine3 (the cowl)
HC = np.array([0, E('HC_Y', '-0.20'), E('HC_Z', '0.57')])
rh = np.linalg.norm(co - HC, axis=1)
hood = P('robe') & (rh < E('HOOD_R', '0.26')) & (np.abs(co[:, 0]) < 0.22)
uh = ss(sj, E('HOOD_LO', '-0.02'), E('HOOD_HI', '0.04')) * (1 - ss(rh, E('HOOD_R', '0.26') - 0.06, E('HOOD_R', '0.26')))
Wn = np.zeros_like(W); lo2 = ss(co[:, 2], zn - 0.03, zn + 0.05)
Wn[:, ix['FHP Neck']] = lo2; Wn[:, ix['FHP Spine3']] = 1 - lo2
cowl = ss(sj, -0.10, -0.02) * (1 - ss(rh, 0.22, 0.30))
q = hood
W[q] = W[q] * (1 - cowl[q])[:, None] + Wn[q] * cowl[q][:, None]
W[q] = W[q] * (1 - uh[q])[:, None]; W[q, ix['FHP Head']] += uh[q]
print('HOOD verts', int(hood.sum()), 'rigid on Head', int((uh[hood] > 0.99).sum()))
# ---- braids on MM9's braid chains, the top on Head
for s_, chain in ((1, ['xpony_a', 'xpony_a1', 'xpony_a2', 'xpony_a3']), (-1, ['xpony', 'xpony1', 'xpony2', 'xpony3'])):
    q = np.where(P('braids') & (co[:, 0] * s_ > 0))[0]
    zs = np.array([MJ[b][2] for b in chain]); zz = co[q, 2]
    i = np.clip(np.searchsorted(-zs, -zz, side='right') - 1, 0, len(zs) - 2)
    t_ = np.clip((zs[i] - zz) / (zs[i] - zs[i + 1]), 0, 1); bi = np.array([ix[b] for b in chain])
    W[q] = 0; np.add.at(W, (q, bi[i]), 1 - t_); np.add.at(W, (q, bi[i + 1]), t_)
    top = ss(zz, zs[1], zs[0]); W[q] *= (1 - top)[:, None]; W[q, ix['FHP Head']] += top
# ---- jewellery: the nearest robe / skirt / head weights, smoothed per piece
if P('jewel').any():
    src = np.where(P('robe') | P('skirt') | P('head'))[0]; kd = cKDTree(co[src]); q = np.where(P('jewel'))[0]
    W[q] = W[src[kd.query(co[q])[1]]]; smooth(P('jewel'), 4)
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
    toe = MJ[pre + 'Toe0']; foot = MJ[pre + 'Foot']
    lv = P('legs') & side; W[lv] = 0
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.05); cw = ss(co[:, 2], foot[2] + 0.02, foot[2] + 0.08)
    W[lv, ix[pre + 'Toe0']] = (tw * (1 - cw))[lv]; W[lv, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[lv]; W[lv, ix[pre + 'Calf']] = cw[lv]
# ---- the shoes and shins also follow the robe's chains (LEGROBE share): MM9 has no legs under the robe, and in the fall its chains
# lift the hem off the floor while the feet stay down, so the shoes came out through the cloth (robe gate Death 7.8 cm)
LR = E('LEGROBE', '0.0')     # tried 0.5: every Walking frame 3.2 cm through the robe, worse
lq = P('legs'); W[lq] = W[lq] * (1 - LR) + Wa[lq] * LR
# ---- symmetric
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix[swap(n)] for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co)
for part in ('skirt', 'robe', 'head'):
    q = P(part); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
print('mirror max', round(float(d[P('skirt') | P('robe')].max()), 5))
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
