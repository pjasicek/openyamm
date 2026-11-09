"""Final weights (PeasantGirl, from PeasantF5's weights_pf5.py, itself from PeasantF8's weights_pf.py: coif for scarf, bare arms for cuffs, bracelets, buckle and ornaments; no ears). Skirt and apron: analytic over MM9's eight skirt chains (azimuth between two neighbouring chains, height between two
neighbouring links of each: exactly four influences, smooth), the waist on XCOM_skirt. Bodice: spine heights, clavicles at the shoulders, the sleeves
by position along the arm (tight elbow). Cuffs: forearm. Head rigid over a neck band; scarf on the head, its hanging back on the Ponytail chain;
ears rigid on the head. Hands: MPFB weights mapped to our finger bones. Legs: Calf, Foot, Toe0. Half-joint helpers split elbow, shoulder, neck.
Mirror symmetric. Args: <asm npz> <mm9 npz> <rig json> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs, SKIRT_CHAINS, SKIRT_MIRROR
A_, M_, R_, OUT = sys.argv[1:5]
D = np.load(A_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
M = np.load(M_); mjn = [str(x) for x in M['jn']]
Rj = json.load(open(R_)); JJ = Rj['joints']; MJ = {k: np.array(v) for k, v in Rj['mm9'].items()}
def J(n): return np.array(JJ[n]) if n in JJ else MJ[n]
names = list(mjn) + [f'Bip01 {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
WAIST = MJ['XCOM_skirt'][2]          # -0.012 in MM9's frame (1.108 over the soles)
# ---- skirt (+ apron): chains by azimuth, links by height
CH = SKIRT_CHAINS
ang = np.array([np.arctan2(MJ[c[-1]][1], MJ[c[-1]][0]) for c in CH]); print('chain angles', np.degrees(ang).round(0).tolist())
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
# ---- torso: spine heights, the pelvis below the waist
Sb = ['XCOM_skirt', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Neck']; Zs = [MJ[b][2] for b in Sb]; Zs[0] = WAIST - 0.03
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.05, 0.11) * ss(co[:, 2], MJ['Bip01 Spine2'][2], MJ['Bip01 Spine2'][2] + 0.07)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'Bip01 {s} Clavicle']] += k
for part in ('skirt', 'lining'):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
for part in ('dress',):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
# ---- arms along the sleeve
sh = J('Bip01 R UpperArm'); el = J('Bip01 R Forearm'); wr = J('Bip01 R Hand'); ax = (wr - sh) / np.linalg.norm(wr - sh)
ELB = float(os.environ.get('ELB', '0.06'))
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = P('dress') & (co[:, 0] * sgn > 0.06) & (r < 0.13) & (t > -0.10)
    pre = f'Bip01 {s} '; Ua, Fa = ix[pre + 'UpperArm'], ix[pre + 'Forearm']
    rt = ss((co - e) @ a, -ELB, ELB)
    w_arm = np.zeros_like(W); w_arm[np.arange(len(co)), Ua] = 1 - rt; w_arm[np.arange(len(co)), Fa] = rt
    bl = ss(t, -0.03, 0.06) * (1 - ss(r, 0.075, 0.11) * (1 - ss(t, 0.10, 0.16)))
    W[arm] = W[arm] * (1 - bl[arm])[:, None] + w_arm[arm] * bl[arm][:, None]
# ---- smoothing on the bodice (the shoulder and waist blends)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('dress') & (co[:, 2] > WAIST + 0.05), int(os.environ.get('UP', '4')))
# ---- band: the nearest skirt/bodice weights, smoothed
src = np.where(P('dress'))[0]; kd = cKDTree(co[src])
for sg_ in (1, -1):
    q = np.where(P('buttons') & (co[:, 0] * sg_ > 0))[0]; W[q] = W[src[kd.query(co[q])[1]]].mean(0)   # each button moves as one piece
# ---- head, neck, ears
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
hv = P('head'); rigid(hv, 'Bip01 Head')
zn = MJ['Bip01 Neck'][2]
# the jaw line as a slanted plane: under the chin (y -0.13) at 1.465 over the soles, rising to the skull base behind; the head shell above it is
# rigid on Head, a 4 cm band blends to Neck, the lowest neck (inside the collar) to Spine3
JY = float(os.environ.get('JAW_Y', '-0.09')); JZ = float(os.environ.get('JAW_Z', '1.060'))
ZC = float(os.environ.get('ZC', '1.050')) - 0.4797
sj = co[:, 2] - 0.233 * (co[:, 1] - JY) - (JZ - 0.4797)
u = ss(sj, -0.02, 0.01) * ss(co[:, 2], ZC, ZC + 0.012); lo = ss(co[:, 2], zn + 0.01, zn + 0.06)   # the level neck seam (ZC) is all Neck, as the dress
neck = hv & (sj < 0.01)
W[neck] = 0; W[neck, ix['Bip01 Head']] = u[neck]; W[neck, ix['Bip01 Neck']] = ((1 - u) * lo)[neck]; W[neck, ix['Bip01 Spine2']] = ((1 - u) * (1 - lo))[neck]
# hair: head; behind the ears it hangs on the Ponytail chain: Head above Ponytail1 + 5 cm, Ponytail1 down to Ponytail11, Ponytail11 below
hv_ = P('hair'); rigid(hv_, 'Bip01 Head')
p1, p11 = J('Bip01 Ponytail1'), J('Bip01 Ponytail11')
bk = ss(co[:, 1], -0.02, 0.04)
wh = ss(co[:, 2], p1[2] - 0.01, p1[2] + 0.05); w11 = 1 - ss(co[:, 2], p11[2], p1[2] - 0.01)
W[hv_] = 0
W[hv_, ix['Bip01 Head']] = (1 - bk * (1 - wh))[hv_]
W[hv_, ix['Bip01 Ponytail1']] = (bk * (1 - wh) * (1 - w11))[hv_]
W[hv_, ix['Bip01 Ponytail11']] = (bk * (1 - wh) * w11)[hv_]
smooth(hv_, 3)
if 'ears' in pid: rigid(P('ears'), 'Bip01 Head')
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
        else: W[v, ix[pre + 'Forearm']] += wt
    if W[v].sum() < 1e-6: W[v, ix[pre + 'Forearm']] = 1
# the stub behind the wrist (hidden in the forearm) rides rigidly on the forearm, blending to the MPFB weights across +-4 mm at the wrist
# under the bracelet: with MPFB's wrist weights it poked up to 5 mm through the forearm skin when the wrist bent (skin_poke_gate.py)
for s_, sg_ in (('R', 1), ('L', -1)):
    pre = f'Bip01 {s_} '; wr_ = J(pre + 'Hand'); fa_ = J(pre + 'Forearm'); fd_ = (wr_ - fa_) / np.linalg.norm(wr_ - fa_)
    q_ = np.where(P('hands') & (co[:, 0] * sg_ > 0))[0]; al_ = (co[q_] - wr_) @ fd_
    k_ = ss(al_, -0.004, 0.004)[:, None]; rig_ = np.zeros((len(q_), W.shape[1])); rig_[:, ix[pre + 'Forearm']] = 1
    W[q_] = W[q_] * k_ + rig_ * (1 - k_)
# ---- legs: toe forward of the ball, foot, calf above the ankle
for s, sgn in (('R', 1), ('L', -1)):
    pre = f'Bip01 {s} '; side = co[:, 0] * sgn > 0
    toe = MJ[pre + 'Toe0']; foot = MJ[pre + 'Foot']
    lv = P('legs') & side; W[lv] = 0
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.05); cw = ss(co[:, 2], foot[2] + 0.02, foot[2] + 0.08)
    W[lv, ix[pre + 'Toe0']] = (tw * (1 - cw))[lv]; W[lv, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[lv]; W[lv, ix[pre + 'Calf']] = cw[lv]
# ---- symmetric (cloth and bodice)
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix[swap(n)] for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co)
for part in ('skirt', 'lining', 'dress', 'hair', 'head'):
    q = P(part); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
print('mirror max', round(float(d[P('skirt') | P('dress')].max()), 5))
# ---- half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('hands') | P('legs') | P('buttons')
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
