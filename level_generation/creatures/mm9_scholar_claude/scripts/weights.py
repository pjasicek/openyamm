"""Final weights. Robe: transferred from MM9's own mesh (nearest triangle, barycentric), then smoothed along the surface; sleeves by position along the arm (tight elbow); hood lining and outer share the head band. Hands: MPFB weights
mapped to our finger bones. Cords: Y chains by arc. Boots leg bones only. Head rigid over a neck band. Half-joint helpers split the elbow, shoulder and neck. Args: <asm npz> <mm9 npz> <rig json> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs
A_, M_, R_, OUT = sys.argv[1:5]
D = np.load(A_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
M = np.load(M_); mco, mtri, mW, mpiece = M['co'], M['tri'], M['W'], M['piece']; mjn = [str(x) for x in M['jn']]
Rj = json.load(open(R_)); JJ = Rj['joints']; MJ = Rj['mm9']
names = list(mjn) + [f'Bip01 {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
P = lambda n: comp == pid[n]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
# ---- robe from MM9's mesh: closest point on the body piece, without hand faces
fingerish = [i for i, n in enumerate(mjn) if 'Finger' in n or n.endswith(' Hand')]
hw = mW[:, fingerish].sum(1)
t0 = mtri[(mpiece[mtri[:, 0]] == 0) & (hw[mtri].max(1) < 0.2)]
mp = mco[t0].mean(1)
def closest(p, tri3):
    a, b, c = tri3[:, 0], tri3[:, 1], tri3[:, 2]
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1); d00, d01, d11 = (ab * ab).sum(1), (ab * ac).sum(1), (ac * ac).sum(1)
    den = d00 * d11 - d01 ** 2; den[np.abs(den) < 1e-14] = 1e-14
    v = (d11 * d1 - d01 * d2) / den; w = (d00 * d2 - d01 * d1) / den
    v = np.clip(v, 0, 1); w = np.clip(w, 0, 1); s = v + w; o = s > 1; v[o] /= s[o]; w[o] /= s[o]
    q = a + ab * v[:, None] + ac * w[:, None]
    return q, np.c_[1 - v - w, v, w]
kd = cKDTree(mp); rob = np.where(P('robe'))[0]
_, cand = kd.query(co[rob], k=8)
best = np.full(len(rob), np.inf); bw = np.zeros((len(rob), 3)); bt = np.zeros(len(rob), int)
for k in range(8):
    tr = mco[t0[cand[:, k]]]; q, bc = closest(co[rob], tr); d = np.linalg.norm(q - co[rob], axis=1); u = d < best
    best[u] = d[u]; bw[u] = bc[u]; bt[u] = cand[u, k]
print('transfer dist p50/p95/max', np.percentile(best, [50, 95, 100]).round(3))
Wm = np.einsum('ni,nij->nj', bw, mW[t0[bt]])
W[rob[:, None], np.arange(len(mjn))] = Wm
# ---- analytic cloth: the eight chains by azimuth, their links by height (a ring at a joint follows that joint; between rings linear), the torso by spine heights. MM9's own weights left lumps once its low-poly rings met our density
CH = [['XFbase', 'XFpiv', 'XFa', 'XFb', 'XFd'], ['Xmain', 'XFRpiv01', 'XFRa01', 'XFRb01', 'XFRc01', 'XFRd01'], ['XRbase01', 'XRpiv01', 'XRb01', 'XRd01'], ['XBRbase01', 'XBRpiv01', 'XBRa01', 'XBRc01', 'XBRd01'], ['XBbase', 'XBa', 'XBc', 'XBd'],
      ['XBRbase', 'XBRpiv', 'XBRa', 'XBRc', 'XBRd'], ['XRbase', 'XRpiv', 'XRb', 'XRd'], ['Xmain', 'XFRpiv', 'XFRa', 'XFRb', 'XFRc', 'XFRd']]
ang = np.array([np.arctan2(MJ[c[-1]][1], MJ[c[-1]][0]) for c in CH]); print('chain angles', np.degrees(ang).round(0).tolist())
th = np.arctan2(co[:, 1], co[:, 0])
order = np.argsort(ang); angS = ang[order]; 
def link_w(chain, z):
    """per vertex: bone index pair and blend for heights z"""
    zs = np.array([MJ[b][2] for b in chain]); zs = np.minimum.accumulate(zs) if False else zs
    i = np.clip(np.searchsorted(-zs, -z, side='right') - 1, 0, len(zs) - 2)
    t = np.clip((zs[i] - z) / np.maximum(zs[i] - zs[i + 1], 1e-4), 0, 1)
    return i, t
Wa = np.zeros((len(co), len(names)))
gap = np.diff(np.r_[angS, angS[0] + 2 * np.pi])
for k in range(len(angS)):
    a0, g0 = angS[k], gap[k]; d0 = (th - a0) % (2 * np.pi); sel = np.where(d0 < g0)[0]
    u = d0[sel] / g0; c0, c1 = CH[order[k]], CH[order[(k + 1) % len(angS)]]
    for ch, wt in ((c0, 1 - u), (c1, u)):
        i, t = link_w(ch, co[sel, 2])
        bi = np.array([ix[b] for b in ch])
        np.add.at(Wa, (sel, bi[i]), wt * (1 - t)); np.add.at(Wa, (sel, bi[i + 1]), wt * t)
# torso: spine heights
Zs = [MJ[b][2] for b in ('Bip01 Spine', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck')]; Bs = [ix[b] for b in ('Bip01 Spine', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck')]
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, 2); t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i])
Wt[np.arange(len(co)), np.array(Bs)[i]] = 1 - t; Wt[np.arange(len(co)), np.array(Bs)[i + 1]] = t
# shoulders on the clavicles
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.10, 0.22) * ss(co[:, 2], 0.30, 0.42)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'Bip01 {s} Clavicle']] += k
k = ss(co[:, 2], 0.125, 0.205)[rob, None]       # chains below the belt, torso above
W[rob] = Wa[rob] * (1 - k) + Wt[rob] * k
# ---- arms by position along the sleeve (both sides)
sh = np.array(JJ['Bip01 R UpperArm']); el = np.array(JJ['Bip01 R Forearm']); wr = np.array(JJ['Bip01 R Hand']); ax = (wr - sh) / np.linalg.norm(wr - sh)
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = P('robe') & (co[:, 0] * sgn > 0.2) & (r < 0.17) & (t > -0.10)
    pre = f'Bip01 {s} '
    Ua, Fa, Cl = ix[pre + 'UpperArm'], ix[pre + 'Forearm'], ix[pre + 'Clavicle']
    tt = (co - e) @ a; rt = ss(tt, -float(os.environ.get('ELB', '0.09')), float(os.environ.get('ELB', '0.09')))
    w_arm = np.zeros_like(W); w_arm[np.arange(len(co)), Ua] = 1 - rt; w_arm[np.arange(len(co)), Fa] = rt
    bl = ss(t, -0.04, 0.09)
    W[arm] = W[arm] * (1 - bl[arm])[:, None] + w_arm[arm] * bl[arm][:, None]
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
# coincident vertices of the shell join in the smoothing
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('robe') & (co[:, 2] < 0.28), int(os.environ.get('RP', '0')))           # lower robe: the low-poly rings of MM9 smoothed out
smooth(P('robe') & (co[:, 2] >= 0.30), int(os.environ.get('UP', '4')))
# ---- symmetric
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    if n in MIRROR: return MIRROR[n]
    return n
MIRROR = {}
for b in ('XRbase', 'XRpiv', 'XRb', 'XRd', 'XBRbase', 'XBRpiv', 'XBRa', 'XBRc', 'XBRd', 'Ytassbase', 'Ytasspiv', 'YtassA', 'YtassB', 'YtassC', 'YtassD', 'XFRpiv', 'XFRa', 'XFRb', 'XFRc', 'XFRd'):
    MIRROR[b] = b + '01'; MIRROR[b + '01'] = b
perm = np.array([ix[swap(n)] for n in names])
d, mm = cKDTree(co * [-1, 1, 1]).query(co); print('mirror max', d[P('robe')].max())
rb = P('robe'); W[rb] = 0.5 * (W[rb] + W[mm[rb]][:, perm])
# ---- hood and head
def only(mask, *bones):
    keep = np.zeros(W.shape[1]); keep[[ix[b] for b in bones]] = 1
    W[mask] *= keep; s = W[mask].sum(1); ids = np.where(mask)[0]; W[ids[s < 1e-6], ix[bones[0]]] = 1
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
# the hood above the shoulders: head, the neck below, the crest on the Ponytail chain; the lining shares the outer's weights by height
hood = P('robe') & (co[:, 2] > 0.575) & (np.abs(co[:, 0]) < 0.17)
u = ss(co[:, 2], 0.60, 0.72)
Wh = np.zeros_like(W); Wh[:, ix['Bip01 Neck']] = 1 - u; Wh[:, ix['Bip01 Head']] = u
kc = ss(co[:, 2], 0.575, 0.635)
W[hood] = W[hood] * (1 - kc[hood])[:, None] + Wh[hood] * kc[hood][:, None]
yy = co[:, 1]; p1, p2, p3 = [np.array(JJ[f'Bip01 Ponytail{k}']) for k in ('1', '11', '12')]
tipw = ss(yy, 0.03, 0.085) * ss(co[:, 2], 0.76, 0.84)
sel = hood & (tipw > 0)
w2 = ss(yy, 0.085, 0.14)
W[sel] = W[sel] * (1 - tipw[sel])[:, None]
W[sel, ix['Bip01 Ponytail11']] += (tipw * (1 - w2))[sel]; W[sel, ix['Bip01 Ponytail12']] += (tipw * w2)[sel]
smooth(P('robe') & (co[:, 2] > 0.58), 3)
hv = P('head'); rigid(hv, 'Bip01 Head')
u = ss(co[:, 2] + 0.45 * (-co[:, 1]), 0.655, 0.735)
neck = hv & (np.hypot(co[:, 0], co[:, 1] + 0.03) < 0.075) & (co[:, 2] < 0.72)
W[neck] = 0; W[neck, ix['Bip01 Neck']] = 1 - u[neck]; W[neck, ix['Bip01 Head']] = u[neck]
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
# ---- boots, shins
for s, sgn in (('R', 1), ('L', -1)):
    pre = f'Bip01 {s} '
    side = co[:, 0] * sgn > 0
    toe = np.array(MJ[pre + 'Toe0']); foot = np.array(MJ[pre + 'Foot'])
    sh_ = P('shoes') & side; W[sh_] = 0
    # toes forward of the ball (-y), Calf at the shaft's top
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.06); cw = ss(co[:, 2], foot[2] + 0.07, foot[2] + 0.13)
    W[sh_, ix[pre + 'Toe0']] = (tw * (1 - cw))[sh_]; W[sh_, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[sh_]; W[sh_, ix[pre + 'Calf']] = cw[sh_]
    rigid(P('shins') & side, pre + 'Calf')
# ---- rope
rob2 = np.where(P('robe'))[0]; kr = cKDTree(co[rob2])
q = np.where(P('belt'))[0]; W[q] = W[rob2[kr.query(co[q])[1]]]
smooth(P('belt'), 30)
only(P('belt'), 'Bip01 Spine', 'Xmain', 'Bip01 Spine2')
for suf, sgn in (('', -1), ('01', 1)):
    chain = [c + suf for c in ('Ytasspiv', 'YtassA', 'YtassB', 'YtassC', 'YtassD')]
    pts = np.array([JJ[c] for c in chain])
    q = np.where((P('cords') | P('knots')) & (co[:, 0] * sgn > 0))[0]
    W[q] = 0
    # the arc along the chain
    seg = pts[1:] - pts[:-1]; L = np.linalg.norm(seg, axis=1)
    pr = np.zeros(len(q)); bestd = np.full(len(q), 1e9)
    acc = np.r_[0, np.cumsum(L)]
    for i in range(len(seg)):
        t_ = np.clip(((co[q] - pts[i]) @ seg[i]) / L[i] ** 2, 0, 1); dd = np.linalg.norm(co[q] - (pts[i] + t_[:, None] * seg[i]), axis=1)
        u_ = dd < bestd; bestd[u_] = dd[u_]; pr[u_] = (acc[i] + t_ * L[i])[u_]
    for n_, v in enumerate(q):
        a = pr[n_]; i = min(np.searchsorted(acc, a, side='right') - 1, len(chain) - 2)
        t_ = (a - acc[i]) / L[i]; t_ = t_ * t_ * (3 - 2 * t_)
        W[v, ix[chain[i]]] = 1 - t_; W[v, ix[chain[i + 1]]] = t_
    top = co[q, 2] > JJ[chain[0]][2]
    W[q[top]] = 0; W[q[top], ix[chain[0]]] = 1
# ---- half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('hands') | P('shoes') | P('shins') | P('cords') | P('knots') | P('belt')
for h, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
    sel = (m_ > 1e-4) & ~rigidp
    W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww = np.where(ww < 0.012, 0, ww); ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
print('WEIGHTS influences', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()), {pn[k]: int((W[comp == k].sum(1) < 1e-5).sum()) for k in range(len(pn)) if (W[comp == k].sum(1) < 1e-5).any()})
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
