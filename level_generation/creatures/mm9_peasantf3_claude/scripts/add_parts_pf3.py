#!/usr/bin/env python3
"""PeasantF3 headwear on the PeasantF1 body (2026-11-02): MM9's PeasantF3.abc is PeasantF1.abc with a long veil hanging down the back
(the hood's tail, MM9 bone Ponytail12, up to 20 cm longer) and two braids from the temples down to the chest (MM9 xpony chains). Torso
and arms are identical, so the F1 body, rig and clips stay; this script adds the two new parts to the frozen mesh.

- veil: a cloth sheet round the back of the head from beside the left jaw to beside the right jaw (PHI degrees either side of the back),
  its top row on the hood (Z_TOP, OFF_TOP outside it) so the hood's lower part is covered, falling to Z_BOT at the back and to Z_SIDE at
  the front ends (MM9's veil reaches 0.24 m, its sides end at the shoulders). Per column the radius from the neck axis is the body's
  (head, hood, bodice within |x| < 0.20 m, so it rests on the shoulders, not the arms) plus a gap growing from OFF_TOP to OFF_BOT, and it
  never falls inward faster than SLOPE (hangs from the hood and approaches the back slowly, as MM9's stiff veil). Radii smoothed.
  Cloth is one-sided: a lining 2.5 mm inside (flipped) and a rim strip closing the free edges, as the sleeve linings.
- braids: a tube along a spline through the temple (under the hood's side edge) and MM9's braid path in front of the shoulders to the
  upper chest, pushed clear of the body by its radius + 4 mm; the radius swells and pinches every half plait (geometry under a painted
  plait), tapers, is tied 2.5 cm above the end and ends in a short tuft; the top end is capped inside the hood.
Args: <asm npz> <posed positions npz (uv_tex2: the tweaked head)> <out asm npz> <report json>   (project folder)"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
A_, U_, OUT, REP = sys.argv[1:5]
A = dict(np.load(A_)); co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]
U = np.load(U_); uco, ucomp = U['co'], U['comp']
PHI, Z_TOP, Z_BOT, Z_SIDE = 105.0, 0.685, 0.255, 0.535
OFF_TOP, OFF_BOT, SLOPE, YC = 0.0015, 0.018, 0.28, 0.0      # pass 2: top flush on the hood (was 4 mm: a ledge), more room on the back (was 12 mm)
NU, NV = 23, 14
# body samples: tweaked positions of head/hood/bodice, densified by triangle centroids and edge midpoints
keep = np.isin(ucomp, [names.index(n) for n in ('head', 'scarf', 'dress')])
ut = U['tri']; tk = keep[ut].all(1)
S = np.vstack([uco[keep], uco[ut[tk]].mean(1), (uco[ut[tk][:, 0]] + uco[ut[tk][:, 1]]) / 2, (uco[ut[tk][:, 1]] + uco[ut[tk][:, 2]]) / 2])
S = S[np.abs(S[:, 0]) < 0.155]
sphi = np.degrees(np.arctan2(S[:, 0], S[:, 1] - YC)); srad = np.hypot(S[:, 0], S[:, 1] - YC)
def body_r(ph, z, dz=0.012, dph=5.0):
    m = (np.abs(S[:, 2] - z) < dz) & (np.abs(((sphi - ph) + 180) % 360 - 180) < dph)
    return srad[m].max() if m.any() else 0.0
u = np.linspace(-1, 1, NU); phis = u * PHI
rep = {}
grid = np.zeros((NV, NU, 3)); R = np.zeros((NV, NU)); Z = np.zeros((NV, NU))
for j, ph in enumerate(phis):
    a = abs(ph) / PHI
    zb = Z_BOT + (Z_SIDE - Z_BOT) * a ** 1.7
    zs = np.linspace(Z_TOP, zb, NV)
    hang = 0.0
    for i, z in enumerate(zs):
        f = (Z_TOP - z) / max(Z_TOP - Z_BOT, 1e-6)
        rb = body_r(ph, z) + OFF_TOP + (OFF_BOT - OFF_TOP) * min(f * 1.6, 1.0)
        if i > 0: hang -= SLOPE * (zs[i - 1] - z)
        r = max(rb, hang); hang = r
        R[i, j] = r; Z[i, j] = z
# smooth the radii (keep the top row's contact with the hood: smooth, then never inside the body + gap)
Rb = R.copy()
for _ in range(6):
    Rp = np.pad(R, 1, mode='edge'); R = 0.4 * R + 0.15 * (Rp[:-2, 1:-1] + Rp[2:, 1:-1] + Rp[1:-1, :-2] + Rp[1:-1, 2:]); R = np.maximum(R, Rb - np.r_[0.0003, 0.001, np.full(NV - 2, 0.002)][:, None])
for j, ph in enumerate(phis):
    t = np.radians(ph); grid[:, j] = np.c_[R[:, j] * np.sin(t), YC + R[:, j] * np.cos(t), Z[:, j]]
# the sheet: quads -> triangles, outward winding (normal away from the axis)
vid = np.arange(NV * NU).reshape(NV, NU)
F = []
for i in range(NV - 1):
    for j in range(NU - 1):
        a, b, c, d = vid[i, j], vid[i, j + 1], vid[i + 1, j + 1], vid[i + 1, j]
        F += [[a, b, c], [a, c, d]]
F = np.array(F); P = grid.reshape(-1, 3)
n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); cen = P[F].mean(1); out = cen.copy(); out[:, 2] = 0; out[:, 1] -= YC
if (np.einsum('ij,ij->i', n, out) < 0).mean() > 0.5: F = F[:, ::-1]
# vertex normals for the lining offset
fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); VN = np.zeros_like(P)
for k in range(3): np.add.at(VN, F[:, k], fn)
VN /= np.maximum(np.linalg.norm(VN, axis=1, keepdims=True), 1e-12)
PL = P - VN * (0.0025 * np.clip(np.repeat(np.arange(NV), NU) / 2.0, 0.25, 1.0))[:, None]      # pass 2: the lining meets the outer sheet at the top edge (no step)
nv0 = len(P)
VP = np.vstack([P, PL]); VF = [F, F[:, ::-1] + nv0]
# rim strip along the sheet's boundary (top row, bottom row, both side columns)
bd = list(vid[0, :]) + list(vid[1:, -1]) + list(vid[-1, ::-1][1:]) + list(vid[::-1, 0][1:-1])
rim = []
for k in range(len(bd)):
    a, b = bd[k], bd[(k + 1) % len(bd)]
    rim += [[a, b, b + nv0], [a, b + nv0, a + nv0]]
rim = np.array(rim)
# orient rim faces outward (away from the sheet centre of their edge's interior)
rc = VP[rim].mean(1); rn = np.cross(VP[rim[:, 1]] - VP[rim[:, 0]], VP[rim[:, 2]] - VP[rim[:, 0]])
inside = P.mean(0)
flip = np.einsum('ij,ij->i', rn, rc - inside) < 0; rim[flip] = rim[flip][:, ::-1]
VF.append(rim)
veil_co = VP; veil_tri = np.vstack(VF)
veil_inner = np.r_[np.zeros(len(F), bool), np.ones(len(F), bool), np.zeros(len(rim), bool)]
veil_uv = np.vstack([np.c_[np.tile(u, NV), np.repeat(np.linspace(0, 1, NV), NU)]] * 2)      # grid parameters (outer and lining share them)
rep['veil'] = {'verts': int(len(veil_co)), 'faces': int(len(veil_tri)), 'r_min': float(R.min()), 'r_max': float(R.max()),
               'bottom_back_z': float(Z[-1, NU // 2]), 'max_gap_back_m': float((R - Rb).max())}
# ---- braids
SB = np.vstack([uco[keep], uco[ut[tk]].mean(1)])
kd = cKDTree(SB)
def spline(pts, n):
    pts = np.array(pts, float); P_ = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]]); out = []
    for k in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[k - 1:k + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1]); return np.array(out)
R0, PITCH, NS = 0.0125, 0.018, 7      # pass 2: 10.5 -> 12.5 mm (the braids read thin once their rings were merged 4 to 1)
LEN_SCALE = 0.82      # 2026-11-02: the full MM9 length ran the braid ends into our fuller bust in Standing and Hit (headwear_gate_pf3.py)
bco, btri, buv = [], [], []
for sgn in (1, -1):
    ctrl = [[0.074, -0.030, 0.680], [0.077, -0.052, 0.610], [0.078, -0.085, 0.540], [0.078, -0.125, 0.465], [0.076, -0.160, 0.400],
            [0.074, -0.178, 0.345]]
    ctrl = [[sgn * c[0], c[1], c[2]] for c in ctrl]
    path = spline(ctrl, 40)
    # arc length, resample every 2.5 mm
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]; s = np.arange(0, L[-1], PITCH / 3)
    s = np.linspace(0, s[-1] * LEN_SCALE, len(s))      # same ring count (the head UVs and paint belong to it), shorter braid
    path = np.c_[[np.interp(s, L, path[:, k]) for k in range(3)]].T
    tot = s[-1]
    def radius(sv):
        r = R0 * (0.75 + 0.25 * np.clip((tot - 0.03 - sv) / 0.06, 0, 1))                  # taper toward the tie
        r = r * (0.94 + 0.08 * np.abs(np.sin(np.pi * sv / (PITCH / 2))))                 # plait swell and pinch
        tie = tot - 0.025; r = np.where(np.abs(sv - tie) < 0.004, R0 * 0.42, r)            # the tie
        tuft = sv > tie + 0.004; q = (sv - tie - 0.004) / max(tot - tie - 0.004, 1e-6)
        r = np.where(tuft, R0 * (0.55 + 0.55 * np.sin(np.pi * np.clip(q, 0, 1) * 0.85)) * (1 - q ** 3), r)
        return np.maximum(r, 0.0008)
    rr = radius(s)
    # clear the body: 4 mm beyond the radius (top end excepted: it starts inside the hood)
    for _ in range(30):
        d, ii = kd.query(path); need = rr + 0.004 - d; push = (need > 0) & (s > 0.03)
        if not push.any(): break
        dirv = path - SB[ii]; dirv /= np.maximum(np.linalg.norm(dirv, axis=1, keepdims=True), 1e-9)
        path[push] += dirv[push] * np.minimum(need[push], 0.002)[:, None]
        for _k in range(2): path[1:-1] = 0.5 * path[1:-1] + 0.25 * (path[:-2] + path[2:])
    d, _ = kd.query(path); rep.setdefault('braid_clear_mm', []).append(float((d - rr)[s > 0.03].min() * 1000))
    T = np.gradient(path, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    ref = np.array([sgn * 1.0, 0, 0]); N0 = []
    for t_ in T:
        nn = ref - (ref @ t_) * t_; nn /= np.linalg.norm(nn); N0.append(nn); ref = nn
    N0 = np.array(N0); B0 = np.cross(T, N0)
    base = len(bco) and sum(len(x) for x in bco)
    ring = []
    th = np.linspace(0, 2 * np.pi, NS, endpoint=False)
    V = (path[:, None, :] + rr[:, None, None] * (np.cos(th)[None, :, None] * N0[:, None, :] + np.sin(th)[None, :, None] * B0[:, None, :])).reshape(-1, 3)
    UVb = np.c_[np.tile(np.r_[th / (2 * np.pi)], len(s)), np.repeat(s / tot, NS)]
    F_ = []
    for i in range(len(s) - 1):
        for k in range(NS):
            a, b, c, d2 = i * NS + k, i * NS + (k + 1) % NS, (i + 1) * NS + (k + 1) % NS, (i + 1) * NS + k
            F_ += [[a, d2, c], [a, c, b]]
    # caps: top (inside the hood) and the tuft's point
    V = np.vstack([V, path[0], path[-1]]); UVb = np.vstack([UVb, [0.5, 0.0], [0.5, 1.0]])
    c0, c1 = len(V) - 2, len(V) - 1; last = (len(s) - 1) * NS
    for k in range(NS):
        F_.append([c0, k, (k + 1) % NS]); F_.append([c1, last + (k + 1) % NS, last + k])
    F_ = np.array(F_)
    # outward winding check on the tube
    fc = V[F_].mean(1); fnn = np.cross(V[F_[:, 1]] - V[F_[:, 0]], V[F_[:, 2]] - V[F_[:, 0]])
    k_ = np.clip(np.searchsorted(s, 0) , 0, None)
    near = cKDTree(path).query(fc)[1]
    if (np.einsum('ij,ij->i', fnn, fc - path[near]) < 0).mean() > 0.5: F_ = F_[:, ::-1]
    bco.append(V); btri.append(F_ + base); buv.append(UVb)
    rep.setdefault('braid_len_m', []).append(float(tot))
bco = np.vstack(bco); btri = np.vstack(btri); buv = np.vstack(buv)
rep['braids'] = {'verts': int(len(bco)), 'faces': int(len(btri))}
# ---- append to the asm
kv, kb = len(names), len(names) + 1
names2 = names + ['veil', 'braids']
n0 = len(co)
A['co'] = np.vstack([co, veil_co, bco]); A['tri'] = np.vstack([tri, veil_tri + n0, btri + n0 + len(veil_co)])
A['comp'] = np.r_[comp, np.full(len(veil_co), kv), np.full(len(bco), kb)]; A['names'] = np.array(names2)
A['f3_inner'] = np.r_[np.zeros(len(tri), bool), veil_inner, np.zeros(len(btri), bool)]
A['f3_param'] = np.vstack([np.full((n0, 2), -1.0), veil_uv, buv])        # sheet / tube parameters (UV seeds)
np.savez(OUT, **A)
rep['asm'] = {'verts': int(len(A['co'])), 'tris': int(len(A['tri'])), 'new_tris': int(len(veil_tri) + len(btri))}
json.dump(rep, open(REP, 'w'), indent=1); print('PARTS', json.dumps(rep))
