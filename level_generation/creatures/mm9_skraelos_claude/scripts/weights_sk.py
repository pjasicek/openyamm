"""Final weights for Skraelos (SKRAELOS.abc's thigh-less human female skeleton), after Igrid's weights_wo.py.
- ROBE below the waist: analytic over MM9's eight skirt chains (azimuth between two neighbouring chains, height between two neighbouring
  links); above the waist spine heights and clavicles; sleeves along the arm (tight elbow), the cuff on the forearm.
- HOOD: rigid on Head above the jaw plane; below it the hood's drape over the shoulders takes the nearest robe weights (a band between).
- HEAD (skull, jaw, teeth, ember eyes): rigid on Head. NECK tube: Head at the top, Neck, Spine3 at the bottom.
- NECKLACE: the nearest robe / hood weights, smoothed along the cord.
- HANDS: every bone piece rigid on its bone (fit_rig_sk.py groups); the big inner palm piece by position Forearm -> Hand.
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
hp = D['hand_piece']
M = np.load(M_); mjn = [str(x) for x in M['jn']]
Rj = json.load(open(R_)); JJ = Rj['joints']; MJ = {k: np.array(v) for k, v in Rj['mm9'].items()}; GR = {int(k): v for k, v in Rj['groups'].items()}
def J(n): return np.array(JJ[n]) if n in JJ else MJ[n]
names = list(mjn) + [f'FHP {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)] + ['FHP R Staff']
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n] if n in pid else np.zeros(len(comp), bool)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
WAIST = MJ['XCOM_skirt'][2]
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
Sb = ['XCOM_skirt', 'FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck']; Zs = [MJ[b][2] for b in Sb]; Zs[0] = WAIST - 0.03
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.06, 0.14) * ss(co[:, 2], MJ['FHP Spine3'][2] - 0.04, MJ['FHP Spine3'][2] + 0.05)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'FHP {s} Clavicle']] += k
q = P('robe'); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
W[q] = Wa[q] * (1 - k) + Wt[q] * k
W[P('cap')] = Wa[P('cap')]
# the cap centre (on the axis) takes the mean of its ring
cq = np.where(P('cap'))[0]; ctr = cq[np.argmin(np.linalg.norm(co[cq, :2] - co[cq, :2].mean(0), axis=1))]; W[ctr] = 0; W[ctr, ix['XCOM_skirt']] = 1
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
    # the cuff's last band follows the wrist a little (CUFF_HAND share at the rim, fading out CUFF_BAND up the sleeve): the staff, rigid in the
    # fist, ran into the cuff lip when the wrist bent (Fidget, Death; orchestrator pre-screen 2026-11-04)
    te = float(t[arm].max()); cu = E('CUFF_HAND', '0.35') * ss(t, te - E('CUFF_BAND', '0.06'), te - 0.005) * arm
    W[:] = W * (1 - cu)[:, None]; W[:, ix[pre + 'Hand']] += cu
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('robe') & (co[:, 2] > WAIST + 0.05), int(E('UP', '4')))
# ---- head: skull rigid; jaw plane under the chin rising to the skull base behind
JS, JZ, JY = E('JAW_SLOPE', '0.30'), E('JAW_Z', '0.56'), E('JAW_Y', '-0.19')
sj = co[:, 2] - JS * (co[:, 1] - JY) - JZ
hv = P('head'); W[hv] = 0; W[hv, ix['FHP Head']] = 1
# neck tube: Head at the top, Neck in the middle, Spine3 at the bottom
nv = P('cowl'); zH, zN = J('FHP Head')[2], MJ['FHP Neck'][2]
u1 = ss(co[:, 2], zN, zH); u0 = ss(co[:, 2], zN - 0.08, zN)
W[nv] = 0; W[nv, ix['FHP Head']] = u1[nv]; W[nv, ix['FHP Neck']] = ((1 - u1) * u0)[nv]; W[nv, ix['FHP Spine3']] = ((1 - u1) * (1 - u0))[nv]
# hood: rigid on Head above the jaw plane, the drape below takes the nearest robe weights
rob = np.where(P('robe'))[0]; kd = cKDTree(co[rob])
hq = np.where(P('hood'))[0]; Wr = W[rob[kd.query(co[hq])[1]]]
uh = ss(sj[hq], E('HOOD_LO', '-0.10'), E('HOOD_HI', '-0.02'))
Wn = np.zeros((len(hq), len(names))); lo2 = ss(co[hq, 2], zN - 0.03, zN + 0.05)
Wn[:, ix['FHP Neck']] = lo2; Wn[:, ix['FHP Spine3']] = 1 - lo2
cl = ss(sj[hq], -0.20, -0.10)
low = Wr * (1 - cl)[:, None] + Wn * cl[:, None]
W[hq] = low * (1 - uh)[:, None]; W[hq, ix['FHP Head']] += uh
smooth(P('hood'), int(E('HOOD_SMOOTH', '3')))
print('HOOD verts', len(hq), 'rigid on Head', int((uh > 0.99).sum()))
# ---- necklace: nearest robe / hood weights, smoothed
nk = np.where(P('necklace'))[0]
if len(nk):
    src = np.where(P('robe') | P('hood'))[0]; kd2 = cKDTree(co[src]); W[nk] = W[src[kd2.query(co[nk])[1]]]; smooth(P('necklace'), 6)
# ---- hands: rigid pieces; the long inner palm piece by position
for v in np.where(P('hands'))[0]:
    k = int(hp[v]); s = 'R' if k >= 0 else 'L'; kk = k if k >= 0 else -k - 1; pre = f'FHP {s} '
    W[v] = 0
    if kk == 7:
        a = ax * ([1, 1, 1] if s == 'R' else [-1, 1, 1]); o = (wr if s == 'R' else wr * [-1, 1, 1])
        u = ss((co[v] - o) @ a, -0.05, 0.0); W[v, ix[pre + 'Hand']] = u; W[v, ix[pre + 'Forearm']] = 1 - u
    else:
        g = GR.get(kk, 'Hand'); W[v, ix[pre + g]] = 1
# ---- staff: rigid on the right Hand (grip_sk.py baked MM9's Standing Finger1 turn into its placement)
W[P('staff')] = 0; W[P('staff'), ix['FHP R Staff']] = 1
W[P('heldskull')] = 0; W[P('heldskull'), ix['FHP L Hand']] = 1
pq = np.where(P('pendant'))[0]
if len(pq):
    nq = np.where(P('necklace'))[0]; W[pq] = W[nq].mean(0) if False else W[nq[cKDTree(co[nq]).query(co[pq].mean(0))[1]]]
# ---- symmetric (robe, hood, head, cowl, necklace)
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix.get(swap(n), ix[n]) for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co)
for part in ('robe', 'hood', 'head', 'cowl', 'necklace', 'cap'):
    q = P(part) & (d < 0.004); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
print('mirror max', round(float(d[P('robe')].max()), 5))
_key = np.round(co, 5); _u, _inv = np.unique(_key, axis=0, return_inverse=True); _inv = _inv.ravel()
_cnt = np.bincount(_inv); _multi = _cnt[_inv] > 1
_acc = np.zeros((len(_u), W.shape[1])); np.add.at(_acc, _inv, W); _avg = _acc / _cnt[:, None]
W[_multi] = _avg[_inv[_multi]]; print('SEAM welded vertices', int(_multi.sum()))
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('hands') | P('head') | P('staff') | P('heldskull') | P('pendant')
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
