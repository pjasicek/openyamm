#!/usr/bin/env python3
"""Igrid geometry tweaks after the paint (positions only, UVs unchanged; no face-shell vertex moves).
1. The circlet gem (Meshy's shield-shaped forehead piece, 3.6 x 3.4 cm, read as a crown ornament): scaled GEMS about its back centre and
   set onto the forehead (MM9's circlet stone is small).
Writes <out asm npz> and <out uv npz> (uv npz co = tweaked asm co[orig]). Args: <asm npz> <uv npz> <out asm npz> <out uv npz>"""
import sys, os
import numpy as np
A, U, OA, OU = sys.argv[1:5]
S = dict(np.load(A)); co, tri, comp = S['co'].copy(), S['tri'], S['comp']; names = [str(x) for x in S['names']]
H = names.index('head'); hv = np.where(comp == H)[0]; ht = tri[np.isin(tri[:, 0], hv)]
par = {v: v for v in hv}
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in ht: r = f(a); par[f(b)] = r; par[f(c)] = r
root = np.array([f(v) for v in hv]); u, cnt = np.unique(root, return_counts=True)
gr = [r for r, n in zip(u, cnt) if n < 200 and abs(co[r, 0]) < 0.03 and co[r, 2] > 0.57 and co[r, 1] < -0.3]
g = hv[np.isin(root, gr)]; G = co[g]
c = G.mean(0); back = c.copy(); back[1] = G[:, 1].max()
GEMS = float(os.environ.get('GEMS', '0.5'))
co[g] = back + (G - back) * GEMS
print('GEM', len(g), 'verts, size', np.ptp(G, 0).round(4), '->', np.ptp(co[g], 0).round(4))
# 2. Legs (review r9: the shoes came out under the robe in Death / Dead, robe gate 7.8 cm): Meshy's shoes are 24 cm boots and the shin tube
#    reached the knee; everything above BOOTTOP over the floor is compressed to BOOTK of its height (low shoes, a short stub inside the hem).
L_ = names.index('legs'); lv = np.where(comp == L_)[0]; Z0 = -0.923; t0 = Z0 + float(os.environ.get('BOOTTOP', '0.09')); BK = float(os.environ.get('BOOTK', '0.12'))
zz = co[lv, 2]; hi = zz > t0; zmax = zz.max()
co[lv[hi], 2] = t0 + (zz[hi] - t0) * BK
print('LEGS top', round(float(zmax), 3), '->', round(float(co[lv, 2].max()), 3))
# 3. The forearm stubs of the grafted hands (inside the cuffs) poked 24 mm through the right sleeve in Fidget (sleeve_poke_gate): the stub
#    behind the wrist is shortened to STUBK of its length and narrowed to STUBN of its radius toward the arm axis.
Hh = names.index('hands'); hv2 = np.where(comp == Hh)[0]; wr0, ax0 = S['wr'], S['ax']
# (r23, 2026-11-04: the jagged collar at the wrists was the stub's cut skin edge showing at the narrowed cuff; the stub is lengthened
#  back to its MPFB length, 1.0 x; 1.4 x stretched it into spikes: the real cause was the uneven wrist ring weights, weights_wo.py)
STUBK, STUBN = float(os.environ.get('STUBK', '1.0')), float(os.environ.get('STUBN', '0.8'))
nst = 0
for sg in (1, -1):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]; q = hv2[co[hv2, 0] * sg > 0]
    al = (co[q] - w) @ a; b = al < -0.005
    rv = co[q] - w - al[:, None] * a
    f = np.clip((-al - 0.005) / 0.02, 0, 1)
    al2 = np.where(b, -0.005 + (al + 0.005) * (1 - (1 - STUBK) * f), al)
    rv2 = rv * np.where(b, 1 - (1 - STUBN) * f, 1)[:, None]
    co[q] = w + al2[:, None] * a + rv2; nst += int(b.sum())
print('STUB verts', nst, 'length x', STUBK, 'radius x', STUBN)
# 3b. STUB CYLINDER (pre-screen r22-r28: the jagged collar at each wrist): MPFB's forearm stub behind the wrist is a sparse cone of
#     long thin triangles (one to four vertices per cm), so seen into the gathered cuff it showed as skin spikes. Every stub vertex behind
#     the wrist (al < STUBA) goes onto a clean cylinder: its angle round the forearm axis kept, its radius the wrist ring's median, its
#     length compressed to STUBLEN behind the wrist (order kept).
STUBA, STUBLEN = float(os.environ.get('STUBA', '-0.004')), float(os.environ.get('STUBLEN', '0.05'))
ncy = 0
for sg in ((1, -1) if os.environ.get('STUBCYL', '1') == '1' else ()):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]; q = hv2[co[hv2, 0] * sg > 0]
    al = (co[q] - w) @ a; rv = co[q] - w - al[:, None] * a; r = np.linalg.norm(rv, axis=1)
    ring = (al > -0.004) & (al < 0.006); rr = float(np.median(r[ring])) if ring.any() else float(np.median(r))
    b = al < STUBA
    if not b.any(): continue
    # r34: one end circle (the cut's zig-zag boundary showed as teeth inside the cuff opening): every stub vertex on the end circle
    al2 = np.full(int(b.sum()), STUBA - STUBLEN)
    co[q[b]] = w + al2[:, None] * a + rv[b] / np.maximum(r[b], 1e-6)[:, None] * rr * 0.97
    # r35 (kept, inactive with STUBA -0.004; r36 with -0.012 grew long spikes): vertices STUBA..-0.002 keep their distance, cylinder radius only
    # (collapsing them too flipped one triangle on top of each wrist: a dark V notch)
    c_ = (al >= STUBA) & (al < -0.002)
    co[q[c_]] = w + al[c_, None] * a + rv[c_] / np.maximum(r[c_], 1e-6)[:, None] * rr * 0.97
    # r37: a stub triangle spanning the ring and the end circle could flip (culled: a dark V notch on top of each wrist): the moved
    # vertices of flipped hand triangles come back toward the wrist (their own distance, at most FLIPMAX behind it), on the cylinder
    co0 = S['co']; ht_ = tri[(comp[tri] == Hh).all(1)]; ht_ = ht_[np.isin(ht_, q[b]).any(1)]
    for _ in range(4):
        n0 = np.cross(co0[ht_[:, 1]] - co0[ht_[:, 0]], co0[ht_[:, 2]] - co0[ht_[:, 0]]); n1 = np.cross(co[ht_[:, 1]] - co[ht_[:, 0]], co[ht_[:, 2]] - co[ht_[:, 0]])
        fl = (n0 * n1).sum(1) < 0
        if not fl.any(): break
        vv = np.intersect1d(np.unique(ht_[fl]), q[b])
        d0 = co0[vv] - w; t0 = np.maximum(d0 @ a, -float(os.environ.get('FLIPMAX', '0.02'))); rv0 = d0 - (d0 @ a)[:, None] * a
        co[vv] = w + t0[:, None] * a + rv0 / np.maximum(np.linalg.norm(rv0, axis=1), 1e-6)[:, None] * rr * 0.97
        print('STUB flipped', int(fl.sum()), 'triangles, verts moved back', len(vv))
    ncy += int(b.sum()); print('STUB CYL', sg, int(b.sum()), 'verts, radius', round(rr, 4))
# 3c. RECENTRE (user review r43: "hands still out of the sleeves": Meshy's bell hangs 3-5 cm in FRONT of MM9's forearm axis, so the
#     forearm left through the bell's back/lower wall and the opening showed its empty inside): the sleeve's last RECL m (robe shell round
#     the forearm) shifts sideways by minus its mean offset from the axis, eased in from RECL to RECL/3 behind the wrist.
RECL = float(os.environ.get('RECL', '0.20'))
if RECL > 0:
    R0_ = names.index('robe'); rv0 = np.where(comp == R0_)[0]
    for sg in (1, -1):
        w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]
        al = (co[rv0] - w) @ a; rv = co[rv0] - w - al[:, None] * a; r = np.linalg.norm(rv, axis=1)
        m = (al > -RECL) & (al < 0.03) & (r < 0.14) & (co[rv0, 0] * sg > 0.25)
        off = rv[m & (al > -0.15)].mean(0)
        u = np.clip((al + RECL) / (RECL * 2 / 3), 0, 1); u = u * u * (3 - 2 * u)
        co[rv0[m]] -= off[None] * u[m, None]
        print('RECENTRE', sg, 'offset', np.round(off, 3), 'verts', int(m.sum()))
# 4. CUFFS (user review r20, 2026-11-04: "her hands are not in her sleeves"): Meshy's bell sleeve opens to a cuff of ~8.5 cm radius around a
#    ~2.5 cm wrist; with MM9's wrist bent 30-60 deg down in Standing, Fidget and Hit, the hand hung from the lower edge of the wide opening
#    and the cuff showed its dark empty inside. The last CUFFL m of each sleeve (robe-shell vertices within 14 cm of the forearm axis, at
#    the wrist end) taper toward the axis to CUFFT of their radius at the rim (smoothstep), so the cuff gathers round the wrist; the stub
#    keeps more of its length (STUBK above) so the wrist visibly enters the cuff.
CUFFL, CUFFT = float(os.environ.get('CUFFL', '0.14')), float(os.environ.get('CUFFT', '0.55'))
R_ = names.index('robe'); rvv = np.where(comp == R_)[0]; ncf = 0
for sg in (1, -1):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]
    al = (co[rvv] - w) @ a; rv = co[rvv] - w - al[:, None] * a; r = np.linalg.norm(rv, axis=1)
    m = (al > -CUFFL - 0.01) & (al < 0.03) & (r < 0.14) & (co[rvv, 0] * sg > 0.25)
    u = np.clip((al + CUFFL) / CUFFL, 0, 1); u = u * u * (3 - 2 * u)
    k = 1 - (1 - CUFFT) * u
    co[rvv[m]] = w + al[m, None] * a + rv[m] * k[m, None]; ncf += int(m.sum())
print('CUFF verts', ncf, 'rim radius x', CUFFT, 'over', CUFFL, 'm')
# 4b. RIM (r42: the relaxation passes are OFF by default, RIMIT 0: relaxing the rolled rim folded it into back faces, see-through sleeves
#     79-85 px; the stretch to RIMEND, the inner-layer push and the rim clearance stay) (orchestrator pre-screen r22: the tapered rim crumpled into a jagged, spiky collar round each wrist: Meshy's hem has teeth and a
#     turned-back cuff band, and the proportional taper folded them over each other). The last RIML m of each sleeve is relaxed: the open rim
#     loop toward its two loop neighbours (an even ring, its teeth gone), the vertices behind it toward all their neighbours, RIMIT passes,
#     easing out over RIML; then nothing within RIMCL of the forearm axis (the rim stays a few mm off the wrist skin).
RIML, RIMIT, RIMCL = float(os.environ.get('RIML', '0.08')), int(os.environ.get('RIMIT', '0')), float(os.environ.get('RIMCL', '0.034'))
rset = set(rvv.tolist()); rt = tri[np.isin(tri, rvv).all(1)]
ed = np.sort(np.vstack([rt[:, [0, 1]], rt[:, [1, 2]], rt[:, [2, 0]]]), axis=1)
ue, cnt = np.unique(ed, axis=0, return_counts=True); bnd = ue[cnt == 1]
nb = {}; bn = {}
for a_, b_ in ue: nb.setdefault(a_, []).append(b_); nb.setdefault(b_, []).append(a_)
for a_, b_ in bnd: bn.setdefault(a_, []).append(b_); bn.setdefault(b_, []).append(a_)
nrim = 0
for sg in (1, -1):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]
    al = (co[rvv] - w) @ a; r = np.linalg.norm(co[rvv] - w - al[:, None] * a, axis=1)
    sel = rvv[(al > -RIML) & (al < 0.04) & (r < 0.14) & (co[rvv, 0] * sg > 0.25)]
    wgt = {v: float(np.clip(((co[v] - w) @ a + RIML) / (RIML * 0.6), 0, 1)) for v in sel}
    for _ in range(RIMIT):
        new = {}
        for v in sel:
            if v in bn and len(bn[v]) == 2: tgt = co[bn[v]].mean(0); k = 0.6
            else: tgt = co[nb[v]].mean(0); k = 0.5 * wgt[v]
            new[v] = co[v] + (tgt - co[v]) * k
        for v, p_ in new.items(): co[v] = p_
    # the relaxation shrinks the open tube end back up the arm (r30: 7.3 cm, the hands hung free again): the relaxed region is stretched
    # back along the forearm axis so its far end sits RIMEND from the wrist joint (r31)
    RIMEND = float(os.environ.get('RIMEND', '-0.010'))
    sl = np.array(sorted(sel)); t_s = (co[sl] - w) @ a; A0 = -RIML; tmax = t_s.max()
    if tmax > A0 + 1e-3:
        t2 = np.where(t_s > A0, A0 + (t_s - A0) * (RIMEND - A0) / (tmax - A0), t_s)
        co[sl] = co[sl] + (t2 - t_s)[:, None] * a
    for v in sel:
        d = co[v] - w; t_ = d @ a; rv_ = d - t_ * a; rr = np.linalg.norm(rv_)
        if rr < RIMCL and t_ > -0.03: co[v] = w + t_ * a + rv_ / max(rr, 1e-6) * RIMCL
    # r33: Meshy's sleeve end also folds an inner layer in toward the axis (robe vertices 0.5-1.8 cm from the forearm axis, 5-10 cm behind
    # the wrist): the wrist and stub skin cut through it, the jagged collar. Every robe vertex of the sleeve end within RIMCL of the axis
    # goes out to RIMCL (inside the sleeve, clear of the skin).
    al_ = (co[rvv] - w) @ a; rv_ = co[rvv] - w - al_[:, None] * a; r_ = np.linalg.norm(rv_, axis=1)
    INNCL = float(os.environ.get('INNCL', '0.029'))      # r41: inside the outer layer (pushed to RIMCL it came through it: back faces, a see-through notch)
    inn = (al_ > -0.16) & (al_ < 0.03) & (r_ < INNCL) & (co[rvv, 0] * sg > 0.25)
    co[rvv[inn]] = w + al_[inn, None] * a + rv_[inn] / np.maximum(r_[inn], 1e-6)[:, None] * INNCL
    print('RIM inner layer pushed out', sg, int(inn.sum()))
    nrim += len(sel); print('RIM', sg, 'verts', len(sel), 'rim loop verts', sum(1 for v in sel if v in bn))
S['co'] = co
D = dict(np.load(U)); D['co'] = co[D['orig']]
# 5. UNDERSLEEVE BAND (orchestrator pre-screen r42, 2026-11-04: a dark V sliver on top of each wrist = the stub's long junction triangles
#    lying almost edge-on at the cuff, `work/hv2/part_raster.py`): a narrow navy undersleeve tube round each wrist coming out of the cuff
#    hides the hand-graft junction in every clip. Per side a tube of BANDN segments at BANDR off the forearm axis from BANDA0 to BANDA1 along
#    the forearm (BANDA1 just behind the wrist joint), a hem folded 3 mm inward with a short inner wall (no view into its back faces); robe
#    part, body material, UVs on a small patch of the gown's navy (`BANDUV`); `band` marks its vertices (weights_wo.py: 100 % Forearm).
BANDN, BANDR, BANDA0, BANDA1 = int(os.environ.get('BANDN', '8')), float(os.environ.get('BANDR', '0.025')), float(os.environ.get('BANDA0', '-0.045')), float(os.environ.get('BANDA1', '-0.004'))
band = np.zeros(len(co), bool)
if BANDN > 0:
    bu0 = np.array([float(v) for v in os.environ.get('BANDUV', '0.7003,0.6674').split(',')])
    ACO, ATRI, ACOMP = [S['co']], [S['tri']], [S['comp']]; UCO, UTRI, UUV, UORIG, UMAT, UCOMP, UINN = [D['co']], [D['tri']], [D['uv']], [D['orig']], [D['mat']], [D['comp']], [D['inner']]
    na, nu = len(S['co']), len(D['co']); R_ = names.index('robe')
    UNDER = os.environ.get('UNDERSLEEVE', '1') == '1'
    import json as _json
    _J = _json.load(open('work/rig.json'))['joints'] if os.path.exists('work/rig.json') else None
    if _J is None: UNDER = False
    for sg in (1, -1):
        w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]
        if UNDER:
            sd = 'R' if sg > 0 else 'L'; e_ = np.array(_J[f'FHP {sd} Forearm']); sh_ = np.array(_J[f'FHP {sd} UpperArm'])
        e1 = np.cross(a, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
        th = np.linspace(0, 2 * np.pi, BANDN, endpoint=False)
        rings = [(BANDA0, BANDR), ((BANDA0 + BANDA1) / 2, BANDR), (BANDA1, BANDR), (BANDA1, BANDR - 0.003)]      # (an inner wall ring, BANDWALL=1, costs 40 faces: LOD0 budget)
        if os.environ.get('BANDWALL', '0') == '1': rings.append((BANDA1 - 0.015, BANDR - 0.003))
        if UNDER:
            # r44 (user review r43: "hands still out of the sleeves": looking into the bell showed its empty inside): the band becomes the cuff
            # of a fitted navy UNDERSLEEVE running up the forearm inside the bell to the elbow and 4 cm up the upper arm (rings from the elbow
            # end to the hem; radii follow the arm, 2.4 cm at the wrist to 3.8 cm past the elbow)
            L_ = float(np.linalg.norm(w - e_)); ue = (e_ - sh_) / np.linalg.norm(e_ - sh_)
            rings = [(-L_ - 0.04 * float(ue @ a), 0.038), (-L_, 0.036), (-L_ + 0.05, 0.033), (-L_ + 0.10, 0.030), (-L_ + 0.15, 0.027), (-0.03, 0.025),
                     (BANDA1, 0.024), (BANDA1, 0.021)]
        V = np.array([w + al_ * a + rr_ * (np.cos(t_) * e1 + np.sin(t_) * e2) for al_, rr_ in rings for t_ in th])
        F = []
        for k in range(len(rings) - 1):
            for i in range(BANDN):
                a0, a1 = k * BANDN + i, k * BANDN + (i + 1) % BANDN; b0, b1 = a0 + BANDN, a1 + BANDN
                F += [[a0, a1, b1], [a0, b1, b0]]
        F = np.array(F)
        # outward winding: flip if the first face's normal points to the axis
        f0 = F[0]; nrm = np.cross(V[f0[1]] - V[f0[0]], V[f0[2]] - V[f0[0]]); cen = V[f0].mean(0) - w; cen -= (cen @ a) * a
        if nrm @ cen < 0: F = F[:, ::-1]
        uvp = bu0 + np.c_[np.tile(np.cos(th), len(rings)), np.repeat(np.arange(len(rings)), BANDN) / len(rings)] * 0.003
        ACO.append(V); ATRI.append(F + na); ACOMP.append(np.full(len(V), R_))
        UCO.append(V); UTRI.append(F + nu); UUV.append(uvp); UORIG.append(np.arange(len(V)) + na); UMAT.append(np.zeros(len(F), int)); UCOMP.append(np.full(len(V), R_)); UINN.append(np.zeros(len(F), bool))
        band = np.r_[band, np.ones(len(V), bool)]
        na += len(V); nu += len(V)
    S['co'] = np.vstack(ACO); S['tri'] = np.vstack(ATRI); S['comp'] = np.concatenate(ACOMP)
    D['co'] = np.vstack(UCO); D['tri'] = np.vstack(UTRI); D['uv'] = np.vstack(UUV); D['orig'] = np.concatenate(UORIG); D['mat'] = np.concatenate(UMAT); D['comp'] = np.concatenate(UCOMP); D['inner'] = np.concatenate(UINN)
    print('BAND', int(band.sum()), 'verts', len(S['tri']) - len(tri), 'faces')
S['band'] = band
# r44: the hand's forearm stub now lies inside the undersleeve: its faces wholly behind the wrist (STUBDEL) are deleted (LOD0 budget)
STUBDEL = float(os.environ.get('STUBDEL', '0.012'))
if BANDN > 0 and STUBDEL > 0:
    cA = S['co']; tA = S['tri']; hid = np.zeros(len(tA), bool)
    for sg in (1, -1):
        w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]; al_v = (cA - w) @ a
        isH = S['comp'] == names.index('hands'); side_v = cA[:, 0] * sg > 0
        hid |= (isH[tA] & side_v[tA] & (al_v[tA] < -STUBDEL)).all(1)
    keep = ~hid
    S['tri'] = tA[keep]; D['tri'] = D['tri'][keep]; D['mat'] = D['mat'][keep]; D['inner'] = D['inner'][keep]
    print('STUB faces deleted', int(hid.sum()))
np.savez(OA, **S); np.savez(OU, **D); print('TWEAKED', OA, OU)
