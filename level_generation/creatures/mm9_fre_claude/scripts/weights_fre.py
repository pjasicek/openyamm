"""Fre copy of weights_pf4.py (2026-11-04): the hair cap (component hood4) takes MM9 Fre's own head weights (MM9F4=work/mm9_fre.npz)
with only its lowest band easing onto the bodice (Z_EASE), and the braid ('braids') rides Head -> Ponytail11 -> Ponytail12 by length as MM9's
braid does. PF4 text follows. PF4 copy of weights_pf4.py (2026-11-02): PeasantF1's weights unchanged for every F1 part, plus the hood and sleeves (section "PF4").
Final weights (PeasantF1). Skirt and apron: analytic over MM9's eight skirt chains (azimuth between two neighbouring chains, height between two
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
names = list(mjn) + [f'FHP {s} {f}{k}' for s in 'LR' for f in FINGERS for k in (1, 2, 3)]
ix = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))
def P(n): return comp == pid[n] if n in pid else np.zeros(len(comp), bool)
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
Sb = ['XCOM_skirt', 'FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck']; Zs = [MJ[b][2] for b in Sb]; Zs[0] = WAIST - 0.03
Wt = np.zeros_like(Wa); z = np.clip(co[:, 2], Zs[0], Zs[-1]); i = np.clip(np.searchsorted(Zs, z, side='right') - 1, 0, len(Zs) - 2)
t = (z - np.array(Zs)[i]) / (np.array(Zs)[i + 1] - np.array(Zs)[i]); Bs = np.array([ix[b] for b in Sb])
Wt[np.arange(len(co)), Bs[i]] = 1 - t; Wt[np.arange(len(co)), Bs[i + 1]] += t
for s, sgn in (('R', 1), ('L', -1)):
    k = ss(co[:, 0] * sgn, 0.07, 0.15) * ss(co[:, 2], MJ['FHP Spine3'][2] - 0.04, MJ['FHP Spine3'][2] + 0.05)
    Wt[:] = Wt * (1 - k)[:, None]; Wt[:, ix[f'FHP {s} Clavicle']] += k
for part in ('skirt', 'lining'):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
for part in ('dress', 'cuffs'):
    q = P(part); k = ss(co[:, 2], WAIST - 0.035, WAIST + 0.01)[q, None]
    W[q] = Wa[q] * (1 - k) + Wt[q] * k
# ---- arms along the sleeve
sh = J('FHP R UpperArm'); el = J('FHP R Forearm'); wr = J('FHP R Hand'); ax = (wr - sh) / np.linalg.norm(wr - sh)
ELB = float(os.environ.get('ELB', '0.06'))
for s, sgn in (('R', 1), ('L', -1)):
    a = ax * [sgn, 1, 1]; o = sh * [sgn, 1, 1]; e = el * [sgn, 1, 1]
    t = (co - o) @ a; r = np.linalg.norm(co - o - t[:, None] * a, axis=1)
    arm = (P('dress') | P('cuffs')) & (co[:, 0] * sgn > 0.08) & (r < 0.16) & (t > -0.10)
    pre = f'FHP {s} '; Ua, Fa = ix[pre + 'UpperArm'], ix[pre + 'Forearm']
    rt = ss((co - e) @ a, -ELB, ELB)
    w_arm = np.zeros_like(W); w_arm[np.arange(len(co)), Ua] = 1 - rt; w_arm[np.arange(len(co)), Fa] = rt
    bl = ss(t, -0.03, 0.07)
    W[arm] = W[arm] * (1 - bl[arm])[:, None] + w_arm[arm] * bl[arm][:, None]
    W[P('cuffs') & (co[:, 0] * sgn > 0)] = w_arm[P('cuffs') & (co[:, 0] * sgn > 0)]
# ---- smoothing on the bodice (the shoulder and waist blends)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
def smooth(mask, passes, k=0.5):
    global W
    for _ in range(passes):
        S = (Ad @ W) / deg[:, None]; W[mask] = (1 - k) * W[mask] + k * S[mask]
smooth(P('dress') & (co[:, 2] > WAIST + 0.05), int(os.environ.get('UP', '4')))
# ---- the cuff's top ring takes the weights of the sleeve ring it meets (the bodice smoothing had opened a crack at the junction)
from collections import defaultdict as _dd
_ec = _dd(int)
for _a, _b, _c in (tri[comp[tri[:, 0]] == pid['cuffs']] if 'cuffs' in pid else []):
    for _e in ((_a, _b), (_b, _c), (_c, _a)): _ec[(min(_e), max(_e))] += 1
if _ec:
    dv = np.where(P('dress'))[0]; cv_ = np.unique([v for _e, _n in _ec.items() if _n == 1 for v in _e]).astype(int); kdc = cKDTree(co[dv]); dd, nn = kdc.query(co[cv_])
    near = dd < 0.012; W[cv_[near]] = W[dv[nn[near]]]; print('CUFF ring welded', int(near.sum()))
# ---- band: the nearest skirt/bodice weights, smoothed
if P('band').any():
    src = np.where(P('skirt') | P('dress'))[0]; kd = cKDTree(co[src]); q = np.where(P('band'))[0]
    W[q] = W[src[kd.query(co[q])[1]]]; smooth(P('band'), 20)
# ---- head, neck, ears
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
hv = P('head'); rigid(hv, 'FHP Head')
zn = MJ['FHP Neck'][2]
# the jaw line as a slanted plane: under the chin (y -0.13) at 1.465 over the soles, rising to the skull base behind; the head shell above it is
# rigid on Head, a 4 cm band blends to Neck, the lowest neck (inside the collar) to Spine3
sj = co[:, 2] - 0.233 * (co[:, 1] + 0.13) - (1.465 - 0.9297)
u = ss(sj, -0.03, 0.01); lo = ss(co[:, 2], zn + 0.01, zn + 0.06)
neck = hv & (sj < 0.01)
W[neck] = 0; W[neck, ix['FHP Head']] = u[neck]; W[neck, ix['FHP Neck']] = ((1 - u) * lo)[neck]; W[neck, ix['FHP Spine3']] = ((1 - u) * (1 - lo))[neck]
rigid(P('ears'), 'FHP Head')
# scarf: head; the hanging back below the crown on Ponytail11 -> 12; the lowest side hems ease toward the neck
sv = P('scarf'); rigid(sv, 'FHP Head')
p11, p12 = J('FHP Ponytail11'), J('FHP Ponytail12')
back = ss(co[:, 1], -0.02, 0.04) * (1 - ss(co[:, 2], p11[2] + 0.03, p11[2] + 0.08))
w2 = ss(co[:, 2], p11[2], p12[2])
W[sv] *= (1 - back[sv])[:, None]; W[sv, ix['FHP Ponytail11']] += (back * (1 - w2))[sv]; W[sv, ix['FHP Ponytail12']] += (back * w2)[sv]
smooth(sv, 3)
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
        elif b0.startswith('upperarm'): W[v, ix[pre + 'UpperArm']] += wt      # PF1: the bare upper arm below the short sleeve
        else: W[v, ix[pre + 'Forearm']] += wt
    if W[v].sum() < 1e-6: W[v, ix[pre + 'Forearm']] = 1
# ---- legs: toe forward of the ball, foot, calf above the ankle
for s, sgn in (('R', 1), ('L', -1)):
    pre = f'FHP {s} '; side = co[:, 0] * sgn > 0
    toe = MJ[pre + 'Toe0']; foot = MJ[pre + 'Foot']
    lv = P('legs') & side; W[lv] = 0
    tw = ss(toe[1] + 0.03 - co[:, 1], 0, 0.05); cw = ss(co[:, 2], foot[2] + 0.02, foot[2] + 0.08)
    W[lv, ix[pre + 'Toe0']] = (tw * (1 - cw))[lv]; W[lv, ix[pre + 'Foot']] = ((1 - tw) * (1 - cw))[lv]; W[lv, ix[pre + 'Calf']] = cw[lv]
# ---- PF4: hood4 (add_parts_pf4.py): MM9 F4's own hood weights (Head; the front lappets on xpony / xpony_a, the back tip on Ponytail11),
# interpolated from the nearest point of MM9's head/hood surface; below the jaw it eases to the bodice's weights (the cape rests on the
# shoulders and back), the opening edge stays rigid on the head; the lining copies its outer twin. sleeve4: each vertex takes the weights of
# the arm under it (same arm coordinate), the bell beyond 0.40 of the forearm the weights of the arm at 0.40 (it hangs from the forearm).
if 'hood4' in pid:
    from scipy.spatial import cKDTree as _K
    M4 = np.load(os.environ.get('MM9F4', 'work/mm9_pf4a.npz')); mco_, mtri_, mW = M4['co'], M4['tri'], M4['W']; mjn4 = [str(x) for x in M4['jn']]
    hb_ = [i for i, n in enumerate(mjn4) if n in ('FHP Head', 'FHP Neck') or n.startswith('xpony') or 'Ponytail' in n]
    mh_ = (mW[:, hb_].sum(1) >= 0.5) & (mco_[:, 2] > 0.44); tH = mtri_[mh_[mtri_].all(1)]
    bw_ = np.array([(i / 8, j / 8, 1 - i / 8 - j / 8) for i in range(9) for j in range(9 - i)])
    Sp = (mco_[tH][:, None, :, :] * bw_[None, :, :, None]).sum(2).reshape(-1, 3)
    SW = (mW[tH][:, None, :, :] * bw_[None, :, :, None]).sum(2).reshape(-1, mW.shape[1])
    q4 = np.where(P('hood4'))[0]; tw4 = D['f4_twin_v'][q4]; outq = q4[tw4 < 0]
    d_, nn_ = _K(Sp).query(co[outq], k=4); wq = 1.0 / np.maximum(d_, 1e-4); wq /= wq.sum(1, keepdims=True)
    Wm = np.zeros((len(outq), len(names)))
    Wmm = (SW[nn_] * wq[..., None]).sum(1)
    for k_, n_ in enumerate(mjn4):
        if n_ in ix: Wm[:, ix[n_]] += Wmm[:, k_]
    Wm /= np.maximum(Wm.sum(1, keepdims=True), 1e-9)
    if os.environ.get('CAP_UNDER', '1') == '1':      # Fre: the hem rides on what lies under it (neck skin at the sides, the bodice/shawl at the back)
        dv = np.where((P('head') & (co[:, 2] < 0.64)) | (P('dress') & (co[:, 2] > WAIST + 0.08)))[0]
    elif os.environ.get('CAP_NECK', '1') == '1':      # the hem copies the neck / jaw skin under it
        dv = np.where(P('head') & (co[:, 2] < 0.64))[0]
    else:
        dv = np.where(P('dress') & (co[:, 2] > WAIST + 0.08))[0]
    Wd = W[dv[_K(co[dv]).query(co[outq])[1]]]
    if os.environ.get('CAP_RINGS'):      # Fre: by ring from the boundary (1 on the outer rings), not by height
        r0, r1 = (float(x) for x in os.environ['CAP_RINGS'].split(',')); Kq = D['f4_param'][P('hood4'), 2].max()
        k = (1 - ss(co[outq, 2], 0.62, 0.70))[:, None] * ss(D['f4_param'][outq, 2], Kq - r0, Kq - r1)[:, None]
    else:
        k = ss(co[outq, 2], *[float(x) for x in os.environ.get('Z_EASE', '0.50,0.56').split(',')])[:, None]      # the cape's lower part rides on the bodice (hem contacts in head turns)
    W[outq] = Wm * k + Wd * (1 - k)
    smooth(P('hood4') & (D['f4_twin_v'] < 0), 4)
    par4 = D['f4_param']; Kh = par4[q4, 2].max()
    edge = P('hood4') & (par4[:, 2] >= Kh - 1) & (D['f4_twin_v'] < 0) & (co[:, 2] > 0.60) & (co[:, 1] < -0.02)
    W[edge] = 0; W[edge, ix['FHP Head']] = 1
    lq = q4[tw4 >= 0]; W[lq] = W[D['f4_twin_v'][lq]]
    print('PF4 hood weighted', len(q4), 'edge rigid', int(edge.sum()))
if 'braids' in pid:
    qb = np.where(P('braids'))[0]; sb = D['fre_braid_s'][qb]; f_ = sb / max(sb.max(), 1e-6)
    if os.environ.get('BRAID_MODE', 'back') == 'mm9':      # MM9's own chain (its clips swing it 13-19 deg into the back)
        hb = 1 - ss(f_, 0.04, 0.12); p12 = ss(f_, 0.70, 0.84); p11 = 1 - hb - p12
        W[qb] = 0; W[qb, ix['FHP Head']] = hb; W[qb, ix['FHP Ponytail11']] = np.maximum(p11, 0); W[qb, ix['FHP Ponytail12']] = p12
    else:      # Fre: a heavy gold-bound braid lying down the back: Head at the root, then the weights of the back under it
        from scipy.spatial import cKDTree as _K2
        dv = np.where(P('dress') & (co[:, 2] > WAIST + 0.10) & (co[:, 1] > 0.03))[0]
        Wb = W[dv[_K2(co[dv]).query(co[qb])[1]]]; Wh = np.zeros_like(Wb); Wh[:, ix['FHP Head']] = 1
        kk = ss(f_, *[float(x) for x in os.environ.get('BRAID_EASE', '0.10,0.40').split(',')])[:, None]
        W[qb] = Wh * (1 - kk) + Wb * kk
    print('FRE braid weighted', len(qb))
if 'hair2' in pid:
    # pass 4: PeasantF2's hair (build_hair_fre.py). The cap is rigid on Head (as F2's); the braid tube rides Head at the tie, then the
    # weights of the back under it (as Fre's own braid did: MM9's Ponytail clips swing a Ponytail-weighted braid into the back) by its
    # fall below the tie (BRAID_EASE fractions of it)
    from scipy.spatial import cKDTree as _K3
    q2 = np.where(P('hair2'))[0]; tb = D['hair2_tube'][q2]; cap2 = q2[~tb]; tub = q2[tb]
    W[cap2] = 0; W[cap2, ix['FHP Head']] = 1
    # r54 cap poke (4 mm from the rim): below the ears and at the nape the skin under the hair's edge rides the neck band (Head -> Neck),
    # so in Walking/Talk/Hit it came 3-5 mm through the rigid rim. Cap rows within HRIM_EASE of the open rim and below 0.645 m take the
    # weights of the nearest face-shell vertex, fading to rigid Head HRIM_EASE in from the rim
    _ky = np.round(co, 5); _, _wi = np.unique(_ky, axis=0, return_inverse=True); _wi = _wi.ravel()
    _ct = tri[np.isin(tri, cap2).all(1)]; _e = np.sort(np.vstack([_wi[_ct[:, [0, 1]]], _wi[_ct[:, [1, 2]]], _wi[_ct[:, [2, 0]]]]), 1)
    _u, _cn = np.unique(_e, axis=0, return_counts=True); _rimr = cap2[np.isin(_wi[cap2], np.unique(_u[_cn == 1]))]
    _dr, _ = _K3(co[_rimr]).query(co[cap2]); HE = float(os.environ.get('HRIM_EASE', '0.025'))
    _kk = (1 - ss(_dr, 0.0, HE)) * (1 - ss(co[cap2, 2], 0.635, 0.655))
    _hv = np.where(P('head') & (co[:, 2] > 0.55))[0]; _Ws = W[_hv[_K3(co[_hv]).query(co[cap2])[1]]]
    W[cap2] = W[cap2] * (1 - _kk[:, None]) + _Ws * _kk[:, None]
    print('FRE hair2 rim rows eased onto the skin', int((_kk > 0.05).sum()))
    if len(tub):
        z = co[tub, 2]; z0 = z.max(); f_ = (z0 - z) / max(z0 - z.min(), 1e-6)
        dv = np.where(P('dress') & (co[:, 2] > WAIST + 0.10) & (co[:, 1] > 0.03))[0]
        Wb = W[dv[_K3(co[dv]).query(co[tub])[1]]]; Wh = np.zeros_like(Wb); Wh[:, ix['FHP Head']] = 1
        kk = ss(f_, *[float(x) for x in os.environ.get('BRAID_EASE', '0.10,0.40').split(',')])[:, None]
        W[tub] = Wh * (1 - kk) + Wb * kk
    print('FRE hair2 weighted: cap', len(cap2), 'braid tube', len(tub))
if 'sleeve4' in pid:
    from scipy.spatial import cKDTree as _K
    q5 = np.where(P('sleeve4'))[0]; par5 = D['f4_param']; side5 = D['f4_side']
    for s, sgn in (('R', 1), ('L', -1)):
        E_ = J('FHP ' + s + ' Forearm'); S_ = J('FHP ' + s + ' UpperArm'); W_ = J('FHP ' + s + ' Hand')
        af = (W_ - E_) / np.linalg.norm(W_ - E_); Lf = np.linalg.norm(W_ - E_); au = (E_ - S_) / np.linalg.norm(E_ - S_); Lu = np.linalg.norm(E_ - S_)
        av = np.where(P('hands') & (co[:, 0] * sgn > 0.10))[0]
        tf = (co[av] - E_) @ af / Lf; tu = (co[av] - E_) @ (-au) / Lu; fa = np.where(tf >= 0, tf, -tu)
        qs = q5[side5[q5] == sgn]; fq = np.minimum(par5[qs, 0], 0.40)
        for v, f_ in zip(qs, fq):
            m_ = np.abs(fa - f_) < 0.06
            if not m_.any(): m_ = np.abs(fa - f_) < 0.15
            cand = av[m_]
            # the arm vertex nearest to the sleeve vertex's direction round the arm, at that arm coordinate
            pv = co[v] if par5[v, 0] <= 0.40 else co[v] - af * (par5[v, 0] - 0.40) * Lf
            W[v] = W[cand[np.argmin(np.linalg.norm(co[cand] - pv, axis=1))]]
    ring_sm = P('sleeve4')
    smooth(ring_sm, 3)
    tw5 = D['f4_twin_v'][q5]; lq = q5[tw5 >= 0]; W[lq] = W[tw5[tw5 >= 0]]
    print('PF4 sleeves weighted', len(q5))
# ---- symmetric (cloth and bodice)
def swap(n):
    if ' L ' in n or ' R ' in n: return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
    return SKIRT_MIRROR.get(n, n)
perm = np.array([ix[swap(n)] for n in names])
_f1 = np.where(~(P('hood4') | P('sleeve4') | P('braids') | P('hair2')))[0]      # PF4: mirror partners among F1's parts only
d, mm = cKDTree(co[_f1] * [-1, 1, 1]).query(co); mm = _f1[mm]
for part in ('skirt', 'lining', 'dress', 'band', 'scarf', 'head'):
    q = P(part); W[q] = 0.5 * (W[q] + W[mm[q]][:, perm])
print('mirror max', round(float(d[P('skirt') | P('dress')].max()), 5))
# ---- PF1: head, hood, bodice and skirt were one Meshy shell split into parts: coincident vertices across a part seam take one averaged
# weight set, so the seams (neck, hairline, waist) cannot open
_key = np.round(co, 5); _u, _inv = np.unique(_key, axis=0, return_inverse=True); _inv = _inv.ravel()
_cnt = np.bincount(_inv); _multi = _cnt[_inv] > 1
_acc = np.zeros((len(_u), W.shape[1])); np.add.at(_acc, _inv, W); _avg = _acc / _cnt[:, None]
W[_multi] = _avg[_inv[_multi]]; print('SEAM welded vertices', int(_multi.sum()))
# ---- half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidp = P('legs') | P('ears')      # PF1: the bare elbow (MPFB arm) takes the half-joint helper too
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
