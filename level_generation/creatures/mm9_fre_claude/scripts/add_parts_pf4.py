#!/usr/bin/env python3
"""PeasantF4 headwear and sleeves on the PeasantF1 body (2026-11-02). MM9's PeasantF4.abc is PeasantF1.abc with a rounder, lower hood that
falls to the shoulders and upper back, and long bell sleeves where F1 has bare forearms (`review/sections.png`, `arms_f1_f4.png`).
F1's frozen mesh keeps every vertex (indices unchanged); new vertices are appended.

- hood4: a new outer hood. Directions from the head centre C are parametrised round a pole behind and above the head (P): rings
  of polar angle up to the boundary curve rho_b(alpha), so the hood is one disk whose single clean boundary is the face opening
  (hugging the head 1.5 mm out, 4 deg beyond F1's hood/head seam, so the seam's zigzag and F1's hood teeth lie under it), the front
  edges beside the jaw and the hem on the shoulders and upper back (MM9 F4's anchors). Radius per direction: the larger of MM9 F4's
  outer surface, our head (+3 mm; F1's old hood only below the crown, so the crown takes MM9's rounder, lower top) and our bodice
  (+8 mm), smoothed. A lining 2.5 mm inside over the outer LIN rings and a rim strip close the cloth (one-sided otherwise).
- F1's hood ('scarf') stays as the skull under it: its free vertices pulled 3 mm inside the new hood where they would reach it;
  its triangles wholly under the new hood's crown are deleted (hidden; LOD0 budget).
- sleeves: the MPFB forearm/upper arm below F1's short sleeve is inflated into a long sleeve (MM9 F4's radius: 3.8 cm at the elbow
  to 4.7 cm at 0.55 of the forearm, never less than the arm + 3 mm), returning to the bare wrist inside the bell; a bell
  (sleeve4) from 0.52 to 0.86 of the forearm flaring to MM9's 5.6 cm, with a lining and a rim.
Args: <asm f1 npz> <uv_tex2 f1 npz (tweaked positions)> <mm9 f4 npz> <rig json> <out asm npz> <report json>"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
A_, U_, M_, R_, OUT, REP = sys.argv[1:7]
A = dict(np.load(A_)); co, tri, comp = A['co'].copy(), A['tri'], A['comp']; names = [str(x) for x in A['names']]
U = np.load(U_); tw = co.copy(); tw[U['orig']] = U['co']           # F1's tweaked positions (the head as shipped)
M = np.load(M_); mco, mtri = M['co'], M['tri']
RJ = json.load(open(R_)); J = {k: np.array(v) for k, v in RJ['mm9'].items()}
rep = {}
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
KH, KS, KD, KA = names.index('head'), names.index('scarf'), names.index('dress'), names.index('hands')
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
cnt_s = np.zeros(inv.max() + 1, int); np.add.at(cnt_s, inv[comp == KS], 1)
cnt_h = np.zeros(inv.max() + 1, int); np.add.at(cnt_h, inv[comp == KH], 1)
seam = ((comp == KH) & (cnt_s[inv] > 0)) | ((comp == KS) & (cnt_h[inv] > 0))
# ================================================================ hood4
C = np.array([0.0, 0.0, 0.665]); Pp = np.array([0.0, 0.5, 0.866]); Pp /= np.linalg.norm(Pp)
E1 = np.array([1.0, 0, 0]); E2 = np.cross(Pp, E1)
def to_ra(X):
    d = X - C; d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    return np.degrees(np.arccos(np.clip(d @ Pp, -1, 1))), np.degrees(np.arctan2(d @ E2, d @ E1))
def dirs(rho, al):
    r, a = np.radians(rho), np.radians(al)
    return np.cos(r)[..., None] * Pp + np.sin(r)[..., None] * (np.cos(a)[..., None] * E1 + np.sin(a)[..., None] * E2)
# boundary: face opening (alpha in (-180, 0)) = F1's seam / old hood + MARGIN; hem (alpha in [0, 180]) from MM9 F4's anchors
MARGIN = 5.5
cons = (seam | (comp == KS)) & (tw[:, 2] > 0.600)
crho, cal = to_ra(tw[cons])
NB = 64
alb = np.linspace(-180, 180, NB, endpoint=False) + 180.0 / NB
def open_req(a):
    d = np.abs(((cal - a) + 180) % 360 - 180); m = d < 9
    return crho[m].max() + MARGIN if m.any() else 0.0
req = np.array([open_req(a) for a in alb])
# MM9 F4's hood hem: its lower edge runs straight from the front corner (xpony_a, 0.115 -0.007 0.543) to the back tip (Ponytail11,
# 0 0.159 0.463), where the hood meets the shoulders
hem_pts = []
for s_ in (1, -1):
    for t_ in np.linspace(0, 1, 7):
        hem_pts.append(np.array([0.115 * s_, -0.007, 0.543]) * (1 - t_) + np.array([0.0, 0.159, 0.463]) * t_)
hr_, ha_ = to_ra(np.array(hem_pts))
o_ = np.argsort(ha_); kx, ky = ha_[o_], hr_[o_]
hem = np.interp(alb, np.r_[kx - 360, kx, kx + 360], np.r_[ky, ky, ky])
hd_ = np.linalg.norm(np.array(hem_pts) - C, axis=1)[o_]
hem_r = np.interp(alb, np.r_[kx - 360, kx, kx + 360], np.r_[hd_, hd_, hd_])     # the hem's distance from C (MM9's lower edge)
for _ in range(4): hem_r = 0.25 * np.roll(hem_r, 1) + 0.5 * hem_r + 0.25 * np.roll(hem_r, -1)
# blend: the opening between -165 and -15, the hem between 5 and 175, the front edges (ear -> corner) the larger of both
wopen = ss(alb, -178, -160) * (1 - ss(alb, -20, -2))
whem = ss(alb, -2, 8) * (1 - ss(alb, 172, 182))
rb = np.where(wopen > 0.5, req, np.where(whem > 0.5, np.maximum(hem, req * (np.abs(alb) < 25)), np.maximum(req, hem)))
for _ in range(3):                                                      # gentle smoothing, never below the opening requirement
    rb = np.maximum(0.25 * np.roll(rb, 1) + 0.5 * rb + 0.25 * np.roll(rb, -1), req * (wopen > 0.01))
hug_b = wopen                                                           # boundary columns that hug the head
rep['boundary'] = {f'{a:.0f}': round(float(r), 1) for a, r in zip(alb[::4], rb[::4])}
# rings: K rings (ring K = boundary, NB columns), inner rings fewer columns (by circumference), a pole vertex
K = int(__import__('os').environ.get('HK', '10'))
rings = []
for k in range(1, K + 1):
    f = k / K; mrho = f * rb.mean(); n = NB if k == K else max(8, int(round(NB * np.sin(np.radians(mrho)) / np.sin(np.radians(rb.mean())) / 2) * 2))
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
    # start both at their first column (angles ascending from -180)
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
# radii
def outer_hit(Vs, Ts, d, reach=0.6):
    t = raycast(C + d * reach, -d, Vs, Ts)
    return np.where(np.isfinite(t), reach - t, 0.0)
def sub(k_list, pos):
    m = np.isin(comp, k_list); t = tri[m[tri].all(1)]; return pos, t
T_mm9 = np.where(np.isfinite(_t := raycast(C, D, mco, mtri)), _t, 0.0)      # MM9 is closed round the head: the first exit from C is the hood's outer surface
Ph, Th = sub([KH], tw); R_head = outer_hit(Ph, Th, D)
Ps, Ts_ = sub([KS], tw); R_old = outer_hit(Ps, Ts_, D)
Pd, Td = sub([KD], tw); R_body = np.where(np.isfinite(_tb := raycast(C, D, Pd, Td)), _tb, 0.0)      # first hit from C (the shoulders, not the arms)
crown = D[:, 2] > 0.30
R_old_c = np.where(crown, 0.0, R_old)
r = np.maximum.reduce([T_mm9, R_head + 0.003, R_old_c + 0.003])
# the cape: over the outer FL rings of the hem columns the radius opens toward MM9's hem line (its hood hangs free of the neck there)
FL = 4
per = lambda arr: (np.r_[alb - 360, alb, alb + 360], np.r_[arr, arr, arr])
wh_v = np.interp(V_al, *per(whem)); hr_v = np.interp(V_al, *per(hem_r)); rb_v = np.interp(V_al, *per(rb))
ref_ids = np.array(ring_ids[K - 1 - FL]); o2 = np.argsort(V_al[ref_ids])
r_ref = np.interp(V_al, V_al[ref_ids][o2], r[ref_ids][o2], period=360)
t_ = np.clip((V_rho / rb_v - (K - FL) / K) / (FL / K), 0, 1)
cape = r_ref + (hr_v - r_ref) * t_
r = np.where(wh_v > 0, np.maximum(r, r * (1 - wh_v) + cape * wh_v), r)
# the bodice: a ray from C meets the shoulders / back from outside, and the cape lies on them, so the hood stays 8 mm before that hit
R_body = np.where(R_body > 0, R_body, np.inf)
hi = R_body - 0.008
r = np.minimum(r, hi)
# the opening edge hugs the head (boundary ring, and the ring before it half way)
bnd = np.array(ring_ids[-1]); pre = np.array(ring_ids[-2])
hug_v = np.zeros(len(r)); hug_v[bnd] = np.interp(V_al[bnd], alb, hug_b)
hug_v[pre] = 0.5 * np.interp(V_al[pre], np.r_[alb - 360, alb, alb + 360], np.r_[hug_b, hug_b, hug_b])
r_hug = np.maximum(R_head, R_old) + 0.0015
low = np.minimum(np.maximum.reduce([R_head + 0.0025, R_old_c + 0.0025, np.where(wh_v > 0.5, cape * 0.97, 0)]), hi)
low = low * (1 - hug_v) + r_hug * hug_v
r = r * (1 - hug_v) + r_hug * hug_v
e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0)
deg = np.bincount(e.ravel(), minlength=len(r))
for _ in range(14):
    acc = np.zeros(len(r)); np.add.at(acc, e[:, 0], r[e[:, 1]]); np.add.at(acc, e[:, 1], r[e[:, 0]])
    rs = 0.5 * r + 0.5 * acc / np.maximum(deg, 1)
    rs = rs * (1 - hug_v) + r_hug * hug_v
    rs[bnd] = rs[bnd] * (1 - wh_v[bnd]) + np.minimum(hr_v[bnd], hi[bnd]) * wh_v[bnd]     # the hem pinned on MM9's hem line
    r = np.minimum(np.maximum(rs, low), hi)
HV = C + D * r[:, None]
if __import__('os').environ.get('DBG'):
    for i in np.array(ring_ids[-1])[::1]:
        print('DBG al %6.1f rho %6.1f T %.3f Rh %.3f Ro %.3f Rb %.3f hr %.3f r %.3f pos %s' % (V_al[i], V_rho[i], T_mm9[i], R_head[i], R_old_c[i], R_body[i], hr_v[i], r[i], np.round(HV[i], 3)))
# outward winding
n = np.cross(HV[F[:, 1]] - HV[F[:, 0]], HV[F[:, 2]] - HV[F[:, 0]]); out = ((HV[F].mean(1) - C) * n).sum(1)
F[out < 0] = F[out < 0][:, ::-1]; rep['hood_flipped'] = int((out < 0).sum())
# lining over the outer LIN rings, 2.5 mm inside, and a rim strip at the boundary
LIN = int(__import__('os').environ.get('HLIN', '2'))
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
# rim winding: its normal points away from the hood's mid surface (outward of the edge): check against the edge direction
hood_co = np.vstack([HV, LV])
mid_edge = hood_co[rimF].mean(1)
n2 = np.cross(hood_co[rimF[:, 1]] - hood_co[rimF[:, 0]], hood_co[rimF[:, 2]] - hood_co[rimF[:, 0]])
# outward of the edge = away from the boundary ring's neighbour on the previous ring (per face)
prev_k = cKDTree(HV[np.array(ring_ids[-2])]); _, pi = prev_k.query(mid_edge); away = mid_edge - HV[np.array(ring_ids[-2])][pi]
flip = (n2 * away).sum(1) < 0; rimF[flip] = rimF[flip][:, ::-1]
hood_F = np.vstack([F, LF, rimF])
hood_inner = np.r_[np.zeros(len(F), bool), np.ones(len(LF), bool), np.zeros(len(rimF), bool)]
hood_rim = np.r_[np.zeros(len(F) + len(LF), bool), np.ones(len(rimF), bool)]
hood_twin_face = np.r_[-np.ones(len(F), int), lin_faces_src, -np.ones(len(rimF), int)]
hood_twin_v = np.r_[-np.ones(len(HV), int), lin_v]
hood_param = np.c_[np.r_[V_rho, V_rho[lin_v]], np.r_[V_al, V_al[lin_v]], np.r_[V_ring, V_ring[lin_v]]]
rep['hood'] = dict(verts=int(len(hood_co)), tris=int(len(hood_F)), outer=int(len(F)), lining=int(len(LF)), rim=int(len(rimF)),
                   r_minus_head_open_mm=float(np.round((r[bnd] - R_head[bnd]).min() * 1000, 2)))
# ---------------- old hood: free vertices pulled inside the new hood; crown triangles under it deleted
s_free = np.where((comp == KS) & ~seam)[0]
d_s = co[s_free] - C; rs = np.linalg.norm(d_s, axis=1); ds = d_s / rs[:, None]
t_new = raycast(C + ds * 0.6, -ds, hood_co, F)
r_new = np.where(np.isfinite(t_new), 0.6 - t_new, np.inf)
pull = rs > r_new - 0.003
co[s_free[pull]] = C + ds[pull] * (r_new[pull] - 0.003)[:, None]
rep['oldhood_pulled'] = int(pull.sum())
# every F1 head / old hood vertex well inside the hood's domain (1 deg past the boundary) and within 2.5 mm of the new hood (or through
# it) is moved 2.5 mm inside it, with its coincident twins (the seam's zigzag and the old hood's teeth poked through between rays)
hv_ = np.where(np.isin(comp, [KH, KS]))[0]
vr_, va_ = to_ra(co[hv_])
rb_at_ = np.interp(va_, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
cand = hv_[vr_ < rb_at_ - 0.2]
d_c = co[cand] - C; r_c = np.linalg.norm(d_c, axis=1); u_c = d_c / r_c[:, None]
t_c = raycast(C + u_c * 0.6, -u_c, hood_co, F); r_h = np.where(np.isfinite(t_c), 0.6 - t_c, np.inf)
bad = r_c > r_h - 0.0025
newpos = C + u_c[bad] * (r_h[bad] - 0.0025)[:, None]
grp = {}
for v, p_ in zip(cand[bad], newpos): grp[inv[v]] = p_
for v in np.where(np.isin(inv, list(grp.keys())))[0]: co[v] = grp[inv[v]]
rep['f1_pushed_under_hood'] = int(bad.sum())
srho, sal = to_ra(co)
rb_at = np.interp(sal, np.r_[alb - 360, alb, alb + 360], np.r_[rb, rb, rb])
hidden_v = (srho < rb_at - 8) & (co[:, 2] > 0.64)
del_tri = (comp[tri[:, 0]] == KS) & hidden_v[tri].all(1) & ~seam[tri].any(1)
rep['oldhood_deleted_tris'] = int(del_tri.sum())
# ================================================================ sleeves (inflate the MPFB arm, add a bell)
sl_co = []; sl_F = []; sl_inner = []; sl_rim = []; sl_twin_face = []; sl_twin_v = []; sl_side = []; sl_param = []
sh, el, wr = J['FHP R UpperArm'], J['FHP R Forearm'], J['FHP R Hand']
Lf = np.linalg.norm(wr - el); Lu = np.linalg.norm(el - sh)
def prof_mm9(f):      # MM9 F4's sleeve radius by forearm fraction (f < 0: upper arm)
    return np.interp(f, [-0.6, 0.0, 0.3, 0.5, 0.7, 0.86], [0.038, 0.038, 0.043, 0.046, 0.051, 0.056])
rep['sleeve'] = {}
def arm_sections(Pv, Tv, E_, au, af, fq_list):
    """Plane sections of the arm surface perpendicular to the local axis: centre and the section points (closest loop to the axis)."""
    out = []
    for fq in fq_list:
        ax = af if fq >= 0 else -au
        p0 = E_ + (af * fq * Lf if fq >= 0 else -au * (-fq) * Lu)
        d = (Pv - p0) @ ax; segs = []
        t_ = Tv[(np.sign(d[Tv]) != np.sign(d[Tv][:, :1])).any(1)]
        for t in t_:
            pts = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                if (d[t[i]] > 0) != (d[t[j]] > 0):
                    w = d[t[i]] / (d[t[i]] - d[t[j]]); pts.append(Pv[t[i]] + w * (Pv[t[j]] - Pv[t[i]]))
            if len(pts) == 2: segs.append(pts)
        S = np.array(segs).reshape(-1, 3)
        S = S[np.linalg.norm(S - p0, axis=1) < 0.09]
        out.append((fq, ax, S.mean(0) if len(S) else p0, S))
    return out
def sec_radius(cq, ax, S, th, ref, ref2):
    rel = S - cq; rel -= (rel @ ax)[:, None] * ax
    ang = np.arctan2(rel @ ref2, rel @ ref); rad = np.linalg.norm(rel, axis=1)
    r = np.array([(rad[_w].max() if (_w := np.abs(((ang - t) + np.pi) % (2 * np.pi) - np.pi) < 0.45).any() else np.nan) for t in th])
    return np.where(np.isnan(r), np.nanmean(r), r)
for s, sgn in (('R', 1), ('L', -1)):
    S_ = sh * [sgn, 1, 1]; E_ = el * [sgn, 1, 1]; W_ = wr * [sgn, 1, 1]
    au = (E_ - S_) / Lu; af = (W_ - E_) / Lf
    arm_t = tri[(comp[tri] == KA).all(1) & (co[tri[:, 0], 0] * sgn > 0.10)]
    arm = np.unique(arm_t)
    P = co[arm]
    tf = (P - E_) @ af / Lf; tu = (P - E_) @ (-au) / Lu
    f = np.where(tf >= 0, tf, -tu)
    dv = np.where((comp == KD) & (co[:, 0] * sgn > 0.12))[0]; tdu = (co[dv] - E_) @ (-au) / Lu
    near_axis = np.linalg.norm((co[dv] - E_) - ((co[dv] - E_) @ au)[:, None] * au, axis=1) < 0.08
    f_hem = -float(tdu[near_axis].min())
    stations = np.round(np.arange(-0.70, 0.96, 0.05), 3)
    secs = arm_sections(co, arm_t, E_, au, af, stations)
    cens = np.array([c_ for _, _, c_, _ in secs])
    def cen_at(fv): return np.c_[[np.interp(fv, stations, cens[:, i]) for i in range(3)]].T
    # sleeve tube: from inside F1's short sleeve (f_hem - 0.10) to the bell's open end (F1 = 0.86 of the forearm), round, MM9's radius
    # (3.8 cm at the elbow to 5.6 cm at the end) and never closer than 4 mm to the arm; the arm under it is F1's, unchanged
    MS = 12
    f_start, f1 = f_hem - 0.10, 0.86
    fs = np.r_[np.linspace(f_start, 0.0, 5)[:-1], np.linspace(0.0, f1, 9)]
    NR = len(fs)
    secs2 = arm_sections(co, arm_t, E_, au, af, fs)
    rmean2 = np.array([np.linalg.norm((S2 - c_) - np.outer((S2 - c_) @ a_, a_), axis=1).mean() if len(S2) else 0.03 for _, a_, c_, S2 in secs2])
    # centre line: the arm's section centres up to 0.45, then straight on along the forearm (the bell hangs round the wrist)
    cl = np.array([c_ for _, _, c_, _ in secs2])
    i45 = int(np.searchsorted(fs, 0.45))
    for i in range(i45, NR):
        cl[i] = cl[i45 - 1] + af * (fs[i] - fs[i45 - 1]) * Lf
    # short sleeve inside: the tube's first rings must stay 3 mm inside F1's sleeve (its section round the same centre)
    dress_t = tri[(comp[tri] == KD).all(1) & (co[tri[:, 0], 0] * sgn > 0.10)]
    base_v = len(sl_co)
    ring_pts = []
    for i, (fq, a_, cq_sec, S2) in enumerate(secs2):
        a_ = af if fq >= 0 else -au
        if 0 <= fq < 0.15: a_ = (-au * (0.15 - fq) + af * fq) / 0.15; a_ /= np.linalg.norm(a_)
        ref = np.cross(a_, [0, 0, 1.0]); ref /= np.linalg.norm(ref); ref2 = np.cross(a_, ref)
        th = np.linspace(0, 2 * np.pi, MS, endpoint=False)
        dd = np.cos(th)[:, None] * ref + np.sin(th)[:, None] * ref2
        cq = cl[i]
        r_arm = sec_radius(cq, a_, S2, th, ref, ref2) if len(S2) else np.full(MS, 0.03)
        R = np.maximum(prof_mm9(fq), r_arm.mean() + 0.004)
        r_ = np.maximum(R, r_arm + 0.004)
        if fq < f_hem:
            sd = arm_sections(co, dress_t, E_, au, af, [fq])[0][3]
            if len(sd):
                r_dr = sec_radius(cq, a_, sd, th, ref, ref2)
                r_ = np.minimum(r_, r_dr - 0.003)
        ring_pts.append(cq + dd * r_[:, None])
        sl_param += [(fq, t_) for t_ in th]
    ring_pts = np.array(ring_pts)
    # clearance: every arm vertex in the tube's range at least CLR inside it (interpolated between rings); rings grown where not, then
    # radii smoothed round and along the tube without losing the clearance (the arm sections alone missed the elbow's bumps)
    CLR = 0.0045
    frames = []
    for i, fq in enumerate(fs):
        a_ = af if fq >= 0 else -au
        if 0 <= fq < 0.15: a_ = (-au * (0.15 - fq) + af * fq) / 0.15; a_ /= np.linalg.norm(a_)
        ref = np.cross(a_, [0, 0, 1.0]); ref /= np.linalg.norm(ref); frames.append((a_, ref, np.cross(a_, ref)))
    rad = np.linalg.norm(ring_pts - cl[:, None, :], axis=2)              # NR x MS
    need = np.zeros_like(rad)
    av = arm[(f >= fs[0]) & (f <= min(fs[-1], 0.80))]
    seg = cl[1:] - cl[:-1]; sl2 = (seg ** 2).sum(1)
    for v in av:
        x = co[v]; t = np.clip(((x - cl[:-1]) * seg).sum(1) / sl2, 0, 1); dpt = np.linalg.norm(cl[:-1] + seg * t[:, None] - x, axis=1)
        i = int(np.argmin(dpt)); w = t[i]
        for ii, ww in ((i, 1 - w), (i + 1, w)):
            a_, ref, ref2 = frames[ii]; rel = x - cl[ii]; rel -= (rel @ a_) * a_
            th_v = np.arctan2(rel @ ref2, rel @ ref) % (2 * np.pi); j = int(np.round(th_v / (2 * np.pi / MS))) % MS
            rv = np.linalg.norm(rel) + CLR
            for jj in (j - 1, j, j + 1):
                need[ii, jj % MS] = max(need[ii, jj % MS], rv * (1.0 if jj == j else 0.97))
    rad = np.maximum(rad, need)
    for _ in range(6):
        rs_ = 0.5 * rad + 0.25 * (np.roll(rad, 1, 1) + np.roll(rad, -1, 1))
        rs_[1:-1] = 0.6 * rs_[1:-1] + 0.2 * (rs_[:-2] + rs_[2:])
        rad = np.maximum(rs_, need)
    for i in range(NR):
        u_ = ring_pts[i] - cl[i]; u_ /= np.linalg.norm(u_, axis=1, keepdims=True); ring_pts[i] = cl[i] + u_ * rad[i][:, None]
    rep.setdefault('sleeve_clear', {})[s] = round(float((need - np.linalg.norm(ring_pts - cl[:, None, :], axis=2)).max() * 1000), 2)
    outer = ring_pts.reshape(-1, 3)
    LR = int(np.searchsorted(fs, 0.30))            # the lining covers the tube from ring LR (f ~0.32) to the open end
    cen_r = cl[:, None, :]
    inner_all = cen_r + (ring_pts - cen_r) * (1 - 0.0025 / np.linalg.norm(ring_pts - cen_r, axis=2, keepdims=True))
    inner = inner_all[LR:].reshape(-1, 3); NL = NR - LR
    vid = lambda i, j: base_v + i * MS + (j % MS)
    lid = lambda i, j: base_v + NR * MS + (i - LR) * MS + (j % MS)
    of = []
    for i in range(NR - 1):
        for j in range(MS):
            of += [[vid(i, j), vid(i + 1, j), vid(i + 1, j + 1)], [vid(i, j), vid(i + 1, j + 1), vid(i, j + 1)]]
    of = np.array(of)
    pts = np.vstack([outer, inner]); off = base_v
    nn = np.cross(pts[of[:, 1] - off] - pts[of[:, 0] - off], pts[of[:, 2] - off] - pts[of[:, 0] - off])
    ring_of = (of[:, 0] - off) // MS
    rel_ = pts[of - off].mean(1) - cl[ring_of]
    if (nn * rel_).sum(1).mean() < 0: of = of[:, ::-1]
    lin_src = np.where(ring_of >= LR)[0]
    lf = []
    for k_ in lin_src:
        lf.append([lid((v - off) // MS, (v - off) % MS) for v in of[k_]][::-1])
    lf = np.array(lf)
    rf = []
    for j in range(MS):
        a0, a1 = vid(NR - 1, j), vid(NR - 1, j + 1); b0, b1 = lid(NR - 1, j), lid(NR - 1, j + 1)
        rf += [[a0, b1, a1], [a0, b0, b1]]
    rf = np.array(rf)
    nr_ = np.cross(pts[rf[:, 1] - off] - pts[rf[:, 0] - off], pts[rf[:, 2] - off] - pts[rf[:, 0] - off])
    if (nr_ @ af).mean() < 0: rf = rf[:, ::-1]
    # the arm under the tight part of the tube (f -0.25 .. 0.28) is hidden: its triangles are deleted (LOD0); a cap closes the lining's top
    # ring onto the arm's surface at that ring, so the view up the sleeve ends on cloth, never in the hollow tube
    fa = np.zeros(len(co)); fa[arm] = f
    del_arm = (comp[tri] == KA).all(1) & (co[tri[:, 0], 0] * sgn > 0.10) & (fa[tri] >= -0.25).all(1) & (fa[tri] <= 0.28).all(1)
    del_tri |= del_arm
    a_, ref_, ref2_ = frames[LR]
    th = np.linspace(0, 2 * np.pi, MS, endpoint=False)
    u_l = ring_pts[LR] - cl[LR]; u_l /= np.linalg.norm(u_l, axis=1, keepdims=True)
    sq = arm_sections(co, arm_t, E_, au, af, [fs[LR]])[0][3]
    ang_l = np.arctan2(u_l @ ref2_, u_l @ ref_)
    r_in = sec_radius(cl[LR], a_, sq, ang_l, ref_, ref2_) * 0.97 if len(sq) else np.full(MS, 0.025)
    capring = cl[LR] + u_l * r_in[:, None]
    cid = lambda j: base_v + NR * MS + NL * MS + (j % MS)
    cf = []
    for j in range(MS):
        cf += [[lid(LR, j), cid(j), cid(j + 1)], [lid(LR, j), cid(j + 1), lid(LR, j + 1)]]
    cf = np.array(cf); pts = np.vstack([pts, capring])
    ncf = np.cross(pts[cf[:, 1] - off] - pts[cf[:, 0] - off], pts[cf[:, 2] - off] - pts[cf[:, 0] - off])
    if (ncf @ a_).mean() < 0: cf = cf[:, ::-1]                      # faces down the sleeve (toward the hand)
    nfo = len(sl_F)
    sl_co += list(pts); sl_side += [sgn] * len(pts)
    sl_F += list(of) + list(lf) + list(rf) + list(cf)
    sl_inner += [False] * len(of) + [True] * len(lf) + [False] * len(rf) + [True] * len(cf)
    sl_rim += [False] * (len(of) + len(lf)) + [True] * len(rf) + [False] * len(cf)
    sl_twin_face += [-1] * len(of) + list(nfo + lin_src) + [-1] * len(rf) + [-1] * len(cf)
    sl_twin_v += [-1] * (NR * MS) + list(range(base_v + LR * MS, base_v + NR * MS)) + [-1] * MS
    sl_param += sl_param[-(NL * MS):] + [(fs[LR], t_) for t_ in ang_l]
    rep.setdefault('arm_deleted', {})[s] = int(del_arm.sum())
    rep['sleeve'][s] = dict(f_hem=round(f_hem, 3), rings=int(NR), r_end_cm=round(float(np.linalg.norm(ring_pts[-1] - cl[-1], axis=1).mean() * 100), 2),
                            r_elbow_cm=round(float(np.linalg.norm(ring_pts[4] - cl[4], axis=1).mean() * 100), 2), tris=int(len(of) + len(lf) + len(rf)))
sl_co = np.array(sl_co); sl_F = np.array(sl_F)
# ================================================================ assemble
n0 = len(co)
keep_t = ~del_tri
names2 = names + ['hood4', 'sleeve4']
co2 = np.vstack([co, hood_co, sl_co])
tri2 = np.vstack([tri[keep_t], hood_F + n0, sl_F + n0 + len(hood_co)])
comp2 = np.r_[comp, np.full(len(hood_co), len(names)), np.full(len(sl_co), len(names) + 1)]
nF1 = int(keep_t.sum())
f4_inner = np.r_[np.zeros(nF1, bool), hood_inner, np.array(sl_inner, bool)]
f4_rim = np.r_[np.zeros(nF1, bool), hood_rim, np.array(sl_rim, bool)]
f4_twin_face = np.r_[-np.ones(nF1, int), np.where(hood_twin_face >= 0, hood_twin_face + nF1, -1),
                     np.where(np.array(sl_twin_face) >= 0, np.array(sl_twin_face) + nF1 + len(hood_F), -1)]
f4_twin_v = np.r_[-np.ones(n0, int), np.where(hood_twin_v >= 0, hood_twin_v + n0, -1),
                  np.where(np.array(sl_twin_v) >= 0, np.array(sl_twin_v) + n0 + len(hood_co), -1)]
f4_param = np.zeros((len(co2), 3)); f4_param[n0:n0 + len(hood_co)] = hood_param
sp = np.array(sl_param); f4_param[n0 + len(hood_co):, :2] = sp
f4_side = np.zeros(len(co2)); f4_side[n0 + len(hood_co):] = np.array(sl_side)
out = dict(A); out.update(co=co2, tri=tri2, comp=comp2, names=np.array(names2), f4_inner=f4_inner, f4_rim=f4_rim, f4_twin_face=f4_twin_face,
                         f4_twin_v=f4_twin_v, f4_param=f4_param, f4_side=f4_side, f4_n_f1=np.int64(n0))
np.savez(OUT, **out)
rep['tris'] = dict(f1=int(len(tri)), deleted=int(del_tri.sum()), arm_deleted=rep['arm_deleted'], hood=int(len(hood_F)), sleeves=int(len(sl_F)), total=int(len(tri2)))
json.dump(rep, open(REP, 'w'), indent=1)
print('PARTS', json.dumps(rep['tris']), json.dumps(rep['sleeve']), json.dumps(rep['hood']), 'pulled', rep['oldhood_pulled'])
