#!/usr/bin/env python3
"""Fre (MM9 row 256) on the PeasantF4 body (2026-11-04). MM9's FRE.abc is PeasantF4.abc's body (same 73-joint skeleton and binds;
`mm9_meshcmp.py peasantf4:fre` all regions <= 3.6 cm) with F4's long bell sleeves, but no hood: a smooth rounded hair cap framing the
face down to the jaw, and one braid from the nape down the back (MM9 bones Ponytail11 / Ponytail12). This script starts from
PeasantF4's frozen asm (copied into work/f4/, read only), keeps every F1 row, the decimated skirt lining and F4's sleeve tubes, drops
F4's hood (component 'hood4') and builds:

- the hair cap, again component 'hood4' (so the F4 tool chain - UVs, upload, under-hood push, gates - treats it as the head-set shell):
  F4's disk parametrisation round a pole behind and above the head; boundary = the face opening (F1's head/old-hood seam + MARGIN, hugging
  the head 1.5 mm out, as F4) and, behind and below the ears, a free hem just beyond F1's old hood's lower edge (HEM_MARGIN), so the old
  hood (the hidden skull) is covered everywhere. Radius: MM9 Fre's head surface (first exit from the head centre), never less than our
  head + 3 mm and F1's old hood + 3 mm below the crown (the crown takes MM9's rounder, lower top, as F4), 8 mm before the bodice; over the
  outer FL rings of the hem the radius is held at the ring before (hair hanging, not tucking onto the neck). A lining over the outer LIN
  rings and a rim close the cloth-like shell.
- one braid ('braids'): F3's plaited tube (7 sides, swelling and pinching every half plait, a tie and a tuft), from inside the cap at the
  nape down the back along a path between MM9's (which leans away from the back) and our back (radius + GAP clear of it).

F1 rows take F1's own positions (asm_frozen_f1; F4's pushes under its hood are undone) and are pushed 2.5 mm under the cap where they
would reach it, as F4 did. Args: <f4 asm> <f1 asm> <f1 uv_tex2 (tweaked)> <mm9 fre npz> <out asm npz> <report json>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
A4_, A1_, U_, M_, OUT, REP = sys.argv[1:7]
A = dict(np.load(A4_)); A1 = np.load(A1_)
names = [str(x) for x in A['names']]
K4, K8 = names.index('hood4'), names.index('sleeve4')
rep = {}
# ---------------------------------------------------------------- drop F4's hood, restore F1's own positions
co0, tri0, comp0 = A['co'].copy(), A['tri'], A['comp']
n1 = len(A1['co']); co0[:n1] = A1['co']
keepv = comp0 != K4
newv = -np.ones(len(co0), int); newv[keepv] = np.arange(keepv.sum())
keepf = ~(comp0[tri0] == K4).any(1)
newf = -np.ones(len(tri0), int); newf[keepf] = np.arange(keepf.sum())
co = co0[keepv]; tri = newv[tri0[keepf]]; comp = comp0[keepv]
assert (tri >= 0).all()
twf0 = A['f4_twin_face'][keepf]; twv0 = A['f4_twin_v'][keepv]
f4_inner = A['f4_inner'][keepf]; f4_rim = A['f4_rim'][keepf]
f4_twin_face = np.where(twf0 >= 0, newf[np.maximum(twf0, 0)], -1)
f4_twin_v = np.where(twv0 >= 0, newv[np.maximum(twv0, 0)], -1)
f4_param = A['f4_param'][keepv]; f4_side = A['f4_side'][keepv]
assert (f4_twin_face[twf0 >= 0] >= 0).all() and (f4_twin_v[twv0 >= 0] >= 0).all()
rep['dropped_hood'] = dict(verts=int((~keepv).sum()), tris=int((~keepf).sum()))
U = np.load(U_); tw = co.copy(); tw[U['orig']] = U['co']           # F1's tweaked positions (the head as shipped)
M = np.load(M_); mco, mtri = M['co'], M['tri']
mco_head = mco
_mjn = [str(x) for x in M['jn']]; _pb = [i for i, n in enumerate(_mjn) if n in ('FHP Ponytail11', 'FHP Ponytail12')]
_onb = M['W'][:, _pb].sum(1) > 0.5
if os.environ.get('NO_MM9_BRAID') == '1': mtri = mtri[~_onb[mtri].any(1)]      # tried (v15): the cap's back pinched into tongues; off. Fre: MM9's braid is left out of MM9's head surface (rays from the head centre left the head through it)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
KH, KS, KD = names.index('head'), names.index('scarf'), names.index('dress')
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
cnt_s = np.zeros(inv.max() + 1, int); np.add.at(cnt_s, inv[comp == KS], 1)
cnt_h = np.zeros(inv.max() + 1, int); np.add.at(cnt_h, inv[comp == KH], 1)
seam = ((comp == KH) & (cnt_s[inv] > 0)) | ((comp == KS) & (cnt_h[inv] > 0))
used = np.zeros(len(co), bool); used[np.unique(tri)] = True
# ---------------------------------------------------------------- the cap
C = np.array([0.0, 0.0, 0.665]); Pp = np.array([0.0, 0.5, 0.866]); Pp /= np.linalg.norm(Pp)
E1 = np.array([1.0, 0, 0]); E2 = np.cross(Pp, E1)
def to_ra(X):
    d = X - C; d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    return np.degrees(np.arccos(np.clip(d @ Pp, -1, 1))), np.degrees(np.arctan2(d @ E2, d @ E1))
def dirs(rho, al):
    r, a = np.radians(rho), np.radians(al)
    return np.cos(r)[..., None] * Pp + np.sin(r)[..., None] * (np.cos(a)[..., None] * E1 + np.sin(a)[..., None] * E2)
MARGIN = float(os.environ.get('MARGIN', '5.5')); HEM_MARGIN = float(os.environ.get('HEM_MARGIN', '4.0'))
NB = int(os.environ.get('NB', '52'))
alb = np.linspace(-180, 180, NB, endpoint=False) + 180.0 / NB
cons_o = (seam | (comp == KS)) & (tw[:, 2] > 0.600) & used           # F4's opening requirement (face side)
crho, cal = to_ra(tw[cons_o])
cons_h = (comp == KS) & used                                          # the whole old hood (hem side)
hrho, hal = to_ra(tw[cons_h])
def req_of(rh, al_, a, m):
    d = np.abs(((al_ - a) + 180) % 360 - 180); w = d < 9
    return rh[w].max() + m if w.any() else 0.0
req = np.array([req_of(crho, cal, a, MARGIN) for a in alb])
# hem: per column the first polar angle whose ray meets our head shell (neck, jaw) at or below Z_HEM (MM9 Fre's cap ends on the nape and
# at the jaw angle); F1's old hood hanging below it is dropped (hidden drape) or pushed under the cap
Z_BACK, Z_SIDE = float(os.environ.get('Z_BACK', '0.575')), float(os.environ.get('Z_SIDE', '0.590'))
_Ph = tw; _Th = tri[(comp[tri] == KH).all(1)]
def _outer(Dd, Vs, Ts, reach=0.6):
    t = raycast(C + Dd * reach, -Dd, Vs, Ts); return np.where(np.isfinite(t), reach - t, 0.0)
_rhos = np.arange(70.0, 175.0, 0.5)
reqh = np.zeros(NB)
for i_, a_ in enumerate(alb):
    zh = Z_SIDE + (Z_BACK - Z_SIDE) * np.abs(np.sin(np.radians(a_)))
    Dd = dirs(_rhos, np.full(len(_rhos), a_)); Rr = np.maximum(_outer(Dd, _Ph, _Th), 0.0)
    Tm = np.where(np.isfinite(_tm := raycast(C, Dd, mco, mtri)), _tm, 0.0)
    Rr = np.where(Rr > 0, Rr, Tm); zz = C[2] + Dd[:, 2] * Rr          # our neck where hit, else MM9's closed head and neck
    ok = (Rr > 0) & (zz <= zh)
    reqh[i_] = _rhos[np.argmax(ok)] if ok.any() else 120.0
from scipy.ndimage import median_filter
reqh = median_filter(reqh, size=5, mode='wrap')
# opening between -165 and -15 (as F4), hem on the rest; the front corners take the larger of both
wopen = ss(alb, -178, -160) * (1 - ss(alb, -20, -2))
rb = np.maximum(req * (wopen > 0.01), reqh * (1 - wopen)) * (wopen < 0.5) + req * (wopen >= 0.5)
for _ in range(3):
    rb = np.maximum(0.25 * np.roll(rb, 1) + 0.5 * rb + 0.25 * np.roll(rb, -1), np.maximum(req * (wopen > 0.01), reqh * (wopen < 0.99)))
rb_topo = rb.copy()      # ring vertex counts come from this boundary (pass 3: the hair's shape changes, its topology and paid UVs must not)
if os.environ.get('HAIR_BACK'):
    # pass 3 (user, r36: "the hair is like cut into the face"): the hair is drawn back. Its edge may not reach below ZS (ear-lobe height) at the
    # sides nor below ZB at the back: per column the boundary stops where our skin (or MM9's head) is at that height; the opening is not
    # widened anywhere (min with the old boundary). A smooth column falloff, no corner.
    ZS, ZB = (float(x) for x in os.environ['HAIR_BACK'].split(','))
    zcap = np.zeros(NB)
    for i_, a_ in enumerate(alb):
        side = np.abs(np.cos(np.radians(a_)))                     # 1 at the sides (alpha 0 / 180), 0 front and back
        back = np.clip(np.sin(np.radians(a_)), 0, 1)              # 1 at the nape (alpha 90)
        zh = ZB * back + ZS * (1 - back) if np.sin(np.radians(a_)) > 0 else ZS
        Dd = dirs(_rhos, np.full(len(_rhos), a_)); Rr = np.maximum(_outer(Dd, _Ph, _Th), 0.0)
        Tm = np.where(np.isfinite(_tm := raycast(C, Dd, mco, mtri)), _tm, 0.0)
        Rr = np.maximum(Rr, Tm) + 0.004; zz = C[2] + Dd[:, 2] * Rr; ok = (Rr > 0.004) & (zz <= zh)      # where the CAP (outside skin and MM9) reaches zh
        zcap[i_] = _rhos[np.argmax(ok)] if ok.any() else 180.0
    for _ in range(4): zcap = 0.25 * np.roll(zcap, 1) + 0.5 * zcap + 0.25 * np.roll(zcap, -1)
    rb = np.minimum(rb, zcap)
    rep['hair_back_rb'] = {f'{a:.0f}': round(float(r), 1) for a, r in zip(alb[::4], rb[::4])}
if os.environ.get('RB_TOPO'):
    rb_topo = np.load(os.environ['RB_TOPO'])
hug_b = np.ones_like(wopen) if os.environ.get('HUG_ALL', '0') == '1' else wopen      # Fre: the hem hugs the neck and jaw too (MM9's cap is closed onto the neck)
rep['boundary'] = {f'{a:.0f}': round(float(r), 1) for a, r in zip(alb[::4], rb[::4])}
K = int(os.environ.get('HK', '9'))
rings = []
for k in range(1, K + 1):
    f = k / K; mrho = f * rb_topo.mean(); n = NB if k == K else max(8, int(round(NB * np.sin(np.radians(mrho)) / np.sin(np.radians(rb_topo.mean())) / 2) * 2))
    n = min(n, NB)
    a = np.linspace(-180, 180, n, endpoint=False) + 180.0 / NB if n == NB else np.linspace(-180, 180, n, endpoint=False)
    rr = f * np.interp(a, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
    rings.append((a, rr))
V_rho = [0.0]; V_al = [0.0]; V_ring = [0]; ring_ids = []
for k, (a, rr) in enumerate(rings, 1):
    ids = list(range(len(V_rho), len(V_rho) + len(a))); ring_ids.append(ids)
    V_rho += list(rr); V_al += list(a); V_ring += [k] * len(a)
V_rho, V_al, V_ring = np.array(V_rho), np.array(V_al), np.array(V_ring)
F = []
for i in range(len(ring_ids[0])):
    F.append([0, ring_ids[0][i], ring_ids[0][(i + 1) % len(ring_ids[0])]])
def zipper(ia, ib):
    na, nb = len(ia), len(ib); aa = V_al[ia]; ab = V_al[ib]
    i = j = 0; out = []
    while i < na or j < nb:
        na_ = (aa[(i + 1) % na] + (360 if i + 1 >= na else 0)) if i < na else 1e9
        nb_ = (ab[(j + 1) % nb] + (360 if j + 1 >= nb else 0)) if j < nb else 1e9
        if na_ <= nb_:
            out.append([ia[i % na], ia[(i + 1) % na], ib[j % nb]]); i += 1
        else:
            out.append([ia[i % na], ib[(j + 1) % nb], ib[j % nb]]); j += 1
    return out
for k in range(len(ring_ids) - 1):
    F += zipper(ring_ids[k], ring_ids[k + 1])
F = np.array(F)
D = dirs(V_rho, V_al)
def outer_hit(Vs, Ts, d, reach=0.6):
    t = raycast(C + d * reach, -d, Vs, Ts)
    return np.where(np.isfinite(t), reach - t, 0.0)
def sub(k_list, pos):
    m = np.isin(comp, k_list); t = tri[m[tri].all(1)]; return pos, t
T_mm9 = np.where(np.isfinite(_t := raycast(C, D, mco_head, mtri)), _t, 0.0)
Ph, Th = sub([KH], tw); R_head = np.maximum(outer_hit(Ph, Th, D), 0.0)      # a hit behind C (the face seen from the back) is no hit
Ps, Ts_ = sub([KS], tw); R_old = np.maximum(outer_hit(Ps, Ts_, D), 0.0)
Pd, Td = sub([KD], tw); R_body = np.where(np.isfinite(_tb := raycast(C, D, Pd, Td)), _tb, 0.0)
crown = D[:, 2] > 0.30
R_old_c = np.where(crown, 0.0, R_old)
if os.environ.get('OLD_FREE', '1') == '1': R_old_c = np.zeros_like(R_old)      # Fre: the old hood is pushed under the cap everywhere (MM9's cap hugs the skull)
R_head_c = np.where(D[:, 2] > float(os.environ.get('CROWN_Z', '0.30')), 0.0, R_head) if os.environ.get('CROWN_HEAD', '1') == '1' else R_head      # Fre: MM9's round crown; F1's peaked forehead goes under it
r = np.maximum.reduce([T_mm9, R_head_c + 0.003, R_old_c + 0.003])
# hem: over the outer FL rings of the hem columns the radius is held at the ring before (the hair hangs past the old hood's edge)
FL = int(os.environ.get('FL', '0'))
per = lambda arr: (np.r_[alb - 360, alb, alb + 360], np.r_[arr, arr, arr])
whem = 1 - wopen
wh_v = np.interp(V_al, *per(whem))
hang = np.zeros(len(V_al)); t_ = np.zeros(len(V_al))
if FL > 0:
    ref_ids = np.array(ring_ids[K - 1 - FL]); o2 = np.argsort(V_al[ref_ids])
    r_ref = np.interp(V_al, V_al[ref_ids][o2], r[ref_ids][o2], period=360)
    t_ = np.clip((V_ring - (K - FL)) / FL, 0, 1)
    HEM_IN = float(os.environ.get('HEM_IN', '0.97'))
    hang = r_ref * (1 - (1 - HEM_IN) * t_)
    r = np.where(wh_v > 0, np.maximum(r * (1 - wh_v), 0) + np.maximum(r, hang) * wh_v, r)
R_body = np.where(R_body > 0, R_body, np.inf)
hi = R_body - 0.008
r = np.minimum(r, hi)
bnd = np.array(ring_ids[-1]); pre = np.array(ring_ids[-2])
hug_v = np.zeros(len(r)); hug_v[bnd] = np.interp(V_al[bnd], alb, hug_b)
hug_v[pre] = 0.5 * np.interp(V_al[pre], np.r_[alb - 360, alb, alb + 360], np.r_[hug_b, hug_b, hug_b])
wo_v = np.interp(V_al, *per(wopen))
r_hug = np.where(wo_v > 0.5, np.maximum(R_head, R_old), np.where(R_head > 0, R_head, T_mm9)) + 0.0015
low = np.minimum(np.maximum.reduce([R_head_c + 0.0025, R_old_c + 0.0025, np.where(wh_v > 0.5, hang * 0.97 * (t_ > 0), 0)]), hi)
low = low * (1 - hug_v) + r_hug * hug_v
r = r * (1 - hug_v) + r_hug * hug_v
e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0)
deg = np.bincount(e.ravel(), minlength=len(r))
for _ in range(14):
    acc = np.zeros(len(r)); np.add.at(acc, e[:, 0], r[e[:, 1]]); np.add.at(acc, e[:, 1], r[e[:, 0]])
    rs = 0.5 * r + 0.5 * acc / np.maximum(deg, 1)
    rs = rs * (1 - hug_v) + r_hug * hug_v
    r = np.minimum(np.maximum(rs, low), hi)
HV = C + D * r[:, None]
if os.environ.get('DBG2'):
    for i in np.where(r < 0.05)[0][:30]: print('DBG2 ring', V_ring[i], 'al %.1f rho %.1f T %.3f Rh %.3f Rb %.3f hi %.3f low %.3f hug %.2f rhug %.3f r %.3f' % (V_al[i], V_rho[i], T_mm9[i], R_head[i], R_body[i], hi[i], low[i], hug_v[i], r_hug[i], r[i]))
if os.environ.get('DBG'):
    for i in np.array(ring_ids[-1]):
        print('DBG al %6.1f rho %6.1f T %.3f Rh %.3f Ro %.3f Rb %.3f r %.3f pos %s' % (V_al[i], V_rho[i], T_mm9[i], R_head[i], R_old[i], R_body[i], r[i], np.round(HV[i], 3)))
n = np.cross(HV[F[:, 1]] - HV[F[:, 0]], HV[F[:, 2]] - HV[F[:, 0]]); out = ((HV[F].mean(1) - C) * n).sum(1)
F[out < 0] = F[out < 0][:, ::-1]; rep['cap_flipped'] = int((out < 0).sum())
LIN = int(os.environ.get('HLIN', '2'))
lin_ring0 = K - LIN
lin_v = np.where(V_ring >= lin_ring0)[0]
lmap = -np.ones(len(HV), int); lmap[lin_v] = len(HV) + np.arange(len(lin_v))
nrm = np.zeros_like(HV)
fn = np.cross(HV[F[:, 1]] - HV[F[:, 0]], HV[F[:, 2]] - HV[F[:, 0]])
for c_ in range(3): np.add.at(nrm, F[:, c_], fn)
nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
LV = HV[lin_v] - nrm[lin_v] * 0.0025
lin_faces_src = np.where((V_ring[F] >= lin_ring0).all(1))[0]
LF = lmap[F[lin_faces_src]][:, ::-1]
rimF = []
b = np.array(ring_ids[-1])
for i in range(len(b)):
    a0, a1 = b[i], b[(i + 1) % len(b)]
    rimF += [[a0, lmap[a1], a1], [a0, lmap[a0], lmap[a1]]]
rimF = np.array(rimF)
hood_co = np.vstack([HV, LV])
mid_edge = hood_co[rimF].mean(1)
n2 = np.cross(hood_co[rimF[:, 1]] - hood_co[rimF[:, 0]], hood_co[rimF[:, 2]] - hood_co[rimF[:, 0]])
prev_k = cKDTree(HV[np.array(ring_ids[-2])]); _, pi = prev_k.query(mid_edge); away = mid_edge - HV[np.array(ring_ids[-2])][pi]
flip = (n2 * away).sum(1) < 0; rimF[flip] = rimF[flip][:, ::-1]
hood_F = np.vstack([F, LF, rimF])
hood_inner = np.r_[np.zeros(len(F), bool), np.ones(len(LF), bool), np.zeros(len(rimF), bool)]
hood_rim = np.r_[np.zeros(len(F) + len(LF), bool), np.ones(len(rimF), bool)]
hood_twin_face = np.r_[-np.ones(len(F), int), lin_faces_src, -np.ones(len(rimF), int)]
hood_twin_v = np.r_[-np.ones(len(HV), int), lin_v]
hood_param = np.c_[np.r_[V_rho, V_rho[lin_v]], np.r_[V_al, V_al[lin_v]], np.r_[V_ring, V_ring[lin_v]]]
rep['cap'] = dict(verts=int(len(hood_co)), tris=int(len(hood_F)), outer=int(len(F)), lining=int(len(LF)), rim=int(len(rimF)),
                  hem_z_min=float(HV[bnd, 2].min()), r_minus_head_open_mm=float(np.round((r[bnd] - R_head[bnd]).min() * 1000, 2)))
# ---------------- F1 rows under the cap: the old hood's free vertices pulled 3 mm inside, every head / old-hood vertex in the cap's domain
# within 2.5 mm of it (or through it) moved 2.5 mm inside, with its coincident twins (F4's rules)
s_free = np.where((comp == KS) & ~seam)[0]
d_s = co[s_free] - C; rs_ = np.linalg.norm(d_s, axis=1); ds = d_s / rs_[:, None]
t_new = raycast(C + ds * 0.6, -ds, hood_co, F)
r_new = np.where(np.isfinite(t_new), 0.6 - t_new, np.inf)
pull = rs_ > r_new - 0.003
co[s_free[pull]] = C + ds[pull] * (r_new[pull] - 0.003)[:, None]
rep['oldhood_pulled'] = int(pull.sum())
hv_ = np.where(np.isin(comp, [KH, KS]))[0]
vr_, va_ = to_ra(co[hv_])
rb_at_ = np.interp(va_, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
cand = hv_[vr_ < rb_at_ - 0.2]
d_c = co[cand] - C; r_c = np.linalg.norm(d_c, axis=1); u_c = d_c / r_c[:, None]
t_c = raycast(C + u_c * 0.6, -u_c, hood_co, F); r_h = np.where(np.isfinite(t_c), 0.6 - t_c, np.inf)
cd_ = np.zeros(inv.max() + 1, int); np.add.at(cd_, inv[comp == KD], 1)
bad = (r_c > r_h - 0.0025) & (cd_[inv[cand]] == 0) & (r_c - (r_h - 0.0025) < 0.03)      # Fre: the neckline seam with the bodice stays put
newpos = C + u_c[bad] * (r_h[bad] - 0.0025)[:, None]
grp = {}
for v, p_ in zip(cand[bad], newpos): grp[inv[v]] = p_
for v in np.where(np.isin(inv, list(grp.keys())))[0]: co[v] = grp[inv[v]]
rep['f1_pushed_under_cap'] = int(bad.sum())
# F4's shard rule: free old-hood vertices within 3 cm of the cap's outer surface and less than 3 mm inside it go 3 mm inside (smoothed)
ht = F; Hs = HV
fnh = np.cross(Hs[ht[:, 1]] - Hs[ht[:, 0]], Hs[ht[:, 2]] - Hs[ht[:, 0]]); vnh = np.zeros_like(Hs)
for c_ in range(3): np.add.at(vnh, ht[:, c_], fnh)
vnh /= np.maximum(np.linalg.norm(vnh, axis=1, keepdims=True), 1e-12)
S = np.vstack([Hs, Hs[ht].mean(1)]); SN = np.vstack([vnh, fnh / np.maximum(np.linalg.norm(fnh, axis=1, keepdims=True), 1e-12)])
kd = cKDTree(S)
st = tri[(comp[tri] == KS).all(1)]
es = np.unique(np.sort(np.vstack([st[:, [0, 1]], st[:, [1, 2]], st[:, [2, 0]]]), 1), axis=0)
isfree = np.zeros(len(co), bool); isfree[s_free] = True
mt = 0
for it in range(6):
    d, j = kd.query(co[s_free]); s = ((co[s_free] - S[j]) * SN[j]).sum(1)
    bad2 = (d < 0.03) & (s > -0.003)
    if not bad2.any(): break
    disp = np.zeros_like(co); disp[s_free[bad2]] = -(s[bad2] + 0.003)[:, None] * SN[j[bad2]]
    for _ in range(3):
        acc = np.zeros_like(co); cnt = np.zeros(len(co))
        np.add.at(acc, es[:, 0], disp[es[:, 1]]); np.add.at(acc, es[:, 1], disp[es[:, 0]]); np.add.at(cnt, es[:, 0], 1); np.add.at(cnt, es[:, 1], 1)
        sm = acc / np.maximum(cnt, 1)[:, None]
        disp = np.where((np.linalg.norm(sm, axis=1) > np.linalg.norm(disp, axis=1))[:, None] & isfree[:, None], sm, disp)
    co[isfree] += disp[isfree]; mt += int(bad2.sum())
rep['shards_pushed'] = mt
if os.environ.get('OLD_EDGE_IN'):      # pass 3: old-hood vertices near / beyond the drawn-back cap's edge go further in (they rode out by 1 cm in clips)
    _vr, _va = to_ra(co); _rbv = np.interp(_va, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
    _q = np.where((comp == KS) & ~seam & (_vr > _rbv - 6.0))[0]; _dd = co[_q] - C; _rr = np.linalg.norm(_dd, axis=1)
    co[_q] = C + _dd * ((_rr - float(os.environ['OLD_EDGE_IN'])) / _rr)[:, None]; rep['oldhood_edge_in'] = int(len(_q))
# F1's old hood outside the cap (its drape behind the nape and lappets beside the jaw) is dropped where it stands off the head shell
# (centre more than DROP_GAP from it; F4's lappet rule): hidden behind the neck before, now it would hang out below the cap's hem
DROP_GAP = float(os.environ.get('DROP_GAP', '0.006'))
fcen = co[tri].mean(1); frho, fal = to_ra(fcen)
rb_f = np.interp(fal, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
hsv = np.unique(tri[(comp[tri] == KH).all(1)]); dh_f = cKDTree(co[hsv]).query(fcen)[0]
onh = np.zeros(inv.max() + 1, bool); onh[inv[hsv]] = True
backf = (fal > 15) & (fal < 165) if os.environ.get('DROP_BACK_ALL', '1') == '1' else np.zeros(len(fal), bool)
if os.environ.get('DROP_ALL_OUT'): backf = np.ones(len(fal), bool)      # pass 3: the drawn-back hair leaves no old-hood lappet to cover      # behind the ears: any distance
dropf = (comp[tri] == KS).all(1) & (frho > rb_f + float(os.environ.get('DROP_MARGIN', '1.0'))) & ((dh_f > DROP_GAP) | backf) & ~onh[inv[tri]].any(1)
if os.environ.get('DROP_SIDE_SEAM'): dropf |= (comp[tri] == KS).all(1) & (frho > rb_f - 1.0) & (np.abs(fcen[:, 0]) > 0.035)      # pass 3: old-hood strips below the ears
assert not dropf[f4_twin_face[f4_twin_face >= 0]].any()
# and the old hood deep under the cap's crown (hidden skull, LOD0 budget): every corner more than CROWN_DEL degrees inside the cap's boundary
# and above Z_DEL (the lower skull stays: it closes the view up under the bob's hem)
CROWN_DEL, Z_DEL = float(os.environ.get('CROWN_DEL', '18')), float(os.environ.get('Z_DEL', '0.66'))
vrho, val = to_ra(co); rb_v_ = np.interp(val, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
deep = (vrho < rb_v_ - CROWN_DEL) & (co[:, 2] > Z_DEL)
dropc = (comp[tri] == KS).all(1) & deep[tri].all(1) & ~onh[inv[tri]].any(1)
rep['oldhood_crown_dropped_tris'] = int((dropc & ~dropf).sum()); dropf = dropf | dropc
kf = ~dropf; nidx = -np.ones(len(tri), int); nidx[kf] = np.arange(kf.sum())
tri = tri[kf]; f4_inner = f4_inner[kf]; f4_rim = f4_rim[kf]
f4_twin_face = np.where(f4_twin_face[kf] >= 0, nidx[np.maximum(f4_twin_face[kf], 0)], -1)
rep['oldhood_dropped_tris'] = int(dropf.sum())
# ---------------------------------------------------------------- the braid
def spline(pts, n):
    pts = np.array(pts, float); P_ = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]]); out = []
    for k in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[k - 1:k + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1]); return np.array(out)
keepb = np.isin(comp, [KH, KS, KD]) & used
SB = np.vstack([co[keepb], co[tri[keepb[tri].all(1)]].mean(1), HV])
kdb = cKDTree(SB)
R0, PITCH, NS = float(os.environ.get('BR0', '0.0115')), 0.018, int(os.environ.get('BNS', '6'))
GAP = float(os.environ.get('BGAP', '0.006'))
ctrl = json.loads(os.environ.get('BCTRL', '[[0,0.100,0.625],[0,0.120,0.575],[0,0.138,0.520],[0,0.152,0.465],[0,0.162,0.410],[0,0.168,0.360]]'))
path = spline(ctrl, 40)
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]; s_ = np.arange(0, L[-1], PITCH / float(os.environ.get('BRING', '2.4')))
if os.environ.get('BRAID_NRING'): s_ = np.linspace(0, L[-1], int(os.environ['BRAID_NRING']))      # pass 3: the paid head UVs belong to this ring count
path = np.c_[[np.interp(s_, L, path[:, k]) for k in range(3)]].T
tot = s_[-1]
def radius(sv):
    r_ = R0 * (0.80 + 0.20 * np.clip((tot - 0.03 - sv) / 0.08, 0, 1))
    r_ = r_ * (0.94 + 0.08 * np.abs(np.sin(np.pi * sv / (PITCH / 2))))
    tie = tot - 0.025; r_ = np.where(np.abs(sv - tie) < 0.004, R0 * 0.45, r_)
    tuft = sv > tie + 0.004; q = (sv - tie - 0.004) / max(tot - tie - 0.004, 1e-6)
    r_ = np.where(tuft, R0 * (0.55 + 0.55 * np.sin(np.pi * np.clip(q, 0, 1) * 0.85)) * (1 - q ** 3), r_)
    return np.maximum(r_, 0.0008)
rr = radius(s_)
# the cap's surface: the braid's top 3.5 cm stays inside it (the root); below, clear of body and cap by the radius + GAP
cap_t = F
def inside_cap(p):
    d_ = p - C; rp = np.linalg.norm(d_, axis=1); u_ = d_ / rp[:, None]
    t_c = raycast(C + u_ * 0.6, -u_, HV, cap_t); return rp < np.where(np.isfinite(t_c), 0.6 - t_c, 0)
for _ in range(40):
    d, ii = kdb.query(path); need = rr + GAP - d; push = (need > 0) & (s_ > 0.035)
    if not push.any(): break
    dirv = path - SB[ii]; dirv /= np.maximum(np.linalg.norm(dirv, axis=1, keepdims=True), 1e-9)
    path[push] += dirv[push] * np.minimum(need[push], 0.002)[:, None]
    for _k in range(2): path[1:-1] = 0.5 * path[1:-1] + 0.25 * (path[:-2] + path[2:])
d, _ = kdb.query(path)
rep['braid'] = dict(len_m=float(tot), clear_mm=float((d - rr)[s_ > 0.035].min() * 1000), root_inside=bool(inside_cap(path[:1])[0]),
                    inside_top_cm=float(s_[inside_cap(path)].max() * 100) if inside_cap(path).any() else 0.0)
Tn = np.gradient(path, axis=0); Tn /= np.linalg.norm(Tn, axis=1, keepdims=True)
ref = np.array([1.0, 0, 0]); N0 = []
for t__ in Tn:
    nn = ref - (ref @ t__) * t__; nn /= np.linalg.norm(nn); N0.append(nn); ref = nn
N0 = np.array(N0); B0 = np.cross(Tn, N0)
th = np.linspace(0, 2 * np.pi, NS, endpoint=False)
BV = (path[:, None, :] + rr[:, None, None] * (np.cos(th)[None, :, None] * N0[:, None, :] + np.sin(th)[None, :, None] * B0[:, None, :])).reshape(-1, 3)
BUV = np.c_[np.tile(th / (2 * np.pi), len(s_)), np.repeat(s_ / tot, NS)]
BF = []
for i in range(len(s_) - 1):
    for k in range(NS):
        a, b_, c, d2 = i * NS + k, i * NS + (k + 1) % NS, (i + 1) * NS + (k + 1) % NS, (i + 1) * NS + k
        BF += [[a, d2, c], [a, c, b_]]
BV = np.vstack([BV, path[0], path[-1]]); BUV = np.vstack([BUV, [0.5, 0.0], [0.5, 1.0]])
c0, c1 = len(BV) - 2, len(BV) - 1; last = (len(s_) - 1) * NS
for k in range(NS):
    BF.append([c0, k, (k + 1) % NS]); BF.append([c1, last + (k + 1) % NS, last + k])
BF = np.array(BF)
fcn = BV[BF].mean(1); fnn = np.cross(BV[BF[:, 1]] - BV[BF[:, 0]], BV[BF[:, 2]] - BV[BF[:, 0]])
near = cKDTree(path).query(fcn)[1]
if (np.einsum('ij,ij->i', fnn, fcn - path[near]) < 0).mean() > 0.5: BF = BF[:, ::-1]
braid_s = np.r_[np.repeat(s_, NS), 0.0, tot]
rep['braid'].update(verts=int(len(BV)), tris=int(len(BF)))
# ---------------------------------------------------------------- assemble: F1 rows + skirt lining rows + sleeves (as F4), cap, braid
names2 = names + ['braids']; KB = len(names)
n0 = len(co)
co2 = np.vstack([co, hood_co, BV])
tri2 = np.vstack([tri, hood_F + n0, BF + n0 + len(hood_co)])
comp2 = np.r_[comp, np.full(len(hood_co), K4), np.full(len(BV), KB)]
nF = len(tri)
o = dict(A)
o.update(co=co2, tri=tri2, comp=comp2, names=np.array(names2),
         f4_inner=np.r_[f4_inner, hood_inner, np.zeros(len(BF), bool)],
         f4_rim=np.r_[f4_rim, hood_rim, np.zeros(len(BF), bool)],
         f4_twin_face=np.r_[f4_twin_face, np.where(hood_twin_face >= 0, hood_twin_face + nF, -1), -np.ones(len(BF), int)],
         f4_twin_v=np.r_[f4_twin_v, np.where(hood_twin_v >= 0, hood_twin_v + n0, -1), -np.ones(len(BV), int)],
         f4_param=np.vstack([f4_param, hood_param, np.zeros((len(BV), 3))]),
         f4_side=np.r_[f4_side, np.zeros(len(hood_co) + len(BV))],
         fre_braid_s=np.r_[np.full(n0 + len(hood_co), -1.0), braid_s], fre_braid_uv=np.vstack([np.full((n0 + len(hood_co), 2), -1.0), BUV]),
         fre_n_f1=np.int64(n1))
np.savez(OUT, **o)
np.save(OUT.replace('.npz', '_rbtopo.npy'), rb_topo)
rep['tris'] = dict(total=int(len(tri2)), cap=int(len(hood_F)), braid=int(len(BF)), rest=int(nF))
json.dump(rep, open(REP, 'w'), indent=1)
print('PARTS', json.dumps(rep['tris']), json.dumps(rep['cap']), json.dumps(rep['braid']), 'pushed', rep['f1_pushed_under_cap'], 'shards', mt)
