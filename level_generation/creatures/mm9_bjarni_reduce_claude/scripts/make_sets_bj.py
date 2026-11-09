#!/usr/bin/env python3
"""Bjarni (from Markel's make_sets_mk.py, 2026-11-05) keep / group sets. Original doc: Markel keep / group sets (Markel's body: body primitive PeasantM5_A = shirt + belt + trousers/boots, lined at the cuffs and the
belt rim, plus the buckle; head primitive PeasantM5Head = the closed face shell (face, painted beard, ears, neck), the scalp hair
shell, the raised collar ring, two eye pieces and the two MPFB hands). From make_sets_m8d.py (PeasantM8 reduction).
Per installed GLB LOD0 face (file primitive order PeasantM5_A, PeasantM5Head) -> work/glb_sets_<tag>.npz (keep, group, lining,
lined, part, mat, pair) for mpqem.py, and review/sets_<tag>_{body,head,hands}.png.
Parts: body 0 shirt (dominant non-leg bones), 1 legs (Thigh/Calf/Foot/Toe), 2 small pieces (buckle; kept);
head 3 face shell (largest component; exact), 4 hair shell (second; hairline rings exact, the rest group 6), 7 collar ring (exact),
8 eyes (exact), 5 hands (group 1).
Body keeps: collar (within COLLAR of a head-prim face/hair/collar vertex), graft/cuffs (GRAFT / CUFF of a hand vertex), soles, rim
strips, loose linings and their halo, BEARD: body faces with a vertex within BEARD_R of a beard vertex (face shell below the mouth,
the beard gate's contact set), optional SHOULDER, PANEL, DEV (folds), HANDS (hand contact npy), EXTRA (comma list of npy face masks).
Groups: 1 hands, 3 legs, 6 hair, 0 shirt (ladder ratio). Usage: make_sets_m5.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
COLLAR = float(E('COLLAR', '0.01')); GRAFT = float(E('GRAFT', '0.015')); CUFF = float(E('CUFF', '0.04'))
SOLE = float(E('SOLE', '0.012')); HALO = float(E('HALO', '0.006')); FRONT_Z = float(E('FRONT_Z', '0.05'))
HRING = int(E('HRING', '2')); BEARD_R = float(E('BEARD_R', '0.03')); MOUTH_Y = float(E('MOUTH_Y', '1.59'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_bjarni.glb', 'Bjarni')
PR = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
assert PR == ['Bjarni', 'BjarniHead'], PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
tw = np.load(HERE / 'work' / 'twins.npz')
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
nb = len(D[PR[0]]['T'])
mat = np.concatenate([[i] * len(D[k]['T']) for i, k in enumerate(PR)])
zero = np.concatenate([tw[f'zero_{k}'] for k in PR])
lining = tw['lining'].astype(bool) | tw['lining2'].astype(bool); lined = tw['lined'].astype(bool) | tw['lined2'].astype(bool)
pair = np.concatenate([np.where(tw[f'pair_{k}'] >= 0, tw[f'pair_{k}'] + (0 if i == 0 else nb), -1) for i, k in enumerate(PR)])
floor = P[:, 1].min(); V = P[T]; C = V.mean(1)
_, w = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True)
w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]
Jc = np.concatenate([D[k]['J'] for k in PR]); Wc = np.concatenate([D[k]['W'] for k in PR])
dv = np.array([jn[Jc[i][Wc[i].argmax()]] for i in range(len(Jc))])
acc = np.zeros((len(T), len(jn)))
for c in range(3):
    for i in range(4):
        np.add.at(acc, (np.arange(len(T)), Jc[T[:, c], i]), Wc[T[:, c], i])
djn = np.array(jn)[acc.argmax(1)]
part = -np.ones(len(T), int)
legj = np.array([any(k in x for k in ('Thigh', 'Calf', 'Foot', 'Toe')) for x in djn])
# Bjarni body prim by component size: tunic + sleeves 1,118, trousers 1,414, yoke 265, boots 206 + 204, belt 177, the rest small
# (30 necklace beads that carry the painted tusks, medallion, buckle, trouser studs; kept whole)
bcs = sorted(np.unique(fl[mat == 0]), key=lambda c: -(fl == c).sum())
bsz = {c: int((fl == c).sum()) for c in bcs}
for c in bcs:
    m = (mat == 0) & (fl == c); legf = np.mean(legj[m])
    if bsz[c] > 1000:
        part[m] = 1 if legf > 0.5 else 0
    elif bsz[c] > 240 and legf < 0.5:
        part[m] = 11                              # yoke
    elif bsz[c] > 190 and legf > 0.5:
        part[m] = 9                               # boots
    elif bsz[c] > 150:
        part[m] = 10                              # belt
    else:
        part[m] = 2
HANDN = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm')
hcs = sorted(np.unique(fl[mat == 1]), key=lambda c: -(fl == c).sum())
nonhand = []
for c in hcs:
    m = (mat == 1) & (fl == c)
    if np.mean([any(h in x for h in HANDN) for x in djn[m]]) > 0.5:
        part[m] = 5
    else:
        nonhand.append(c)
part[(mat == 1) & (fl == nonhand[0])] = 3          # face/beard/hair shell 2,055
for c in nonhand[1:]:
    part[(mat == 1) & (fl == c)] = 7               # neck/collar pieces 45 + 11 + 11
hc = np.load(HERE / 'work' / 'head_classes_bj.npz')
scalp = np.zeros(len(T), bool); scalp[nb:] = hc['scalp']
part[scalp] = 4                                    # scalp hair (hair-coloured, above the brows or behind the ears)
assert (part >= 0).all()
pv = lambda *ps: np.unique(T[np.isin(part, ps)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
# scalp hairline: HRING rings of scalp faces next to the kept face/beard/sideburn faces of the shell (and the open nape rim)
hair = part == 4
fv = np.zeros(n, bool); fv[FT[part == 3].ravel()] = True
he = np.sort(np.r_[FT[hair][:, [0, 1]], FT[hair][:, [1, 2]], FT[hair][:, [2, 0]]], 1)
k_, c_n = np.unique(he, axis=0, return_counts=True)
bv = np.zeros(n, bool); bv[k_[c_n == 1].ravel()] = True
hl = hair & (fv[FT].any(1) | bv[FT].any(1))
for _ in range(HRING - 1):
    ev = np.zeros(n, bool); ev[FT[hl].ravel()] = True
    hl |= hair & ev[FT].any(1)
keep = np.isin(part, (2, 3, 7, 8)) | hl
# skirt (part 10, the tunic below the belt, its own piece): HEM rings of faces at its open rims stay exact (an opening the
# see-through gate looks into); RIMR > 0: also every cloth face within RIMR m of an open rim of the tunic/yoke/skirt/trousers
for p_ in (10,):
    sm = part == p_
    se = np.sort(np.r_[FT[sm][:, [0, 1]], FT[sm][:, [1, 2]], FT[sm][:, [2, 0]]], 1); k2, c2 = np.unique(se, axis=0, return_counts=True)
    rv = np.zeros(n, bool); rv[k2[c2 == 1].ravel()] = True
    hem = sm & rv[FT].any(1)
    for _ in range(int(E('HEM', '1')) - 1):
        ev = np.zeros(n, bool); ev[FT[hem].ravel()] = True; hem |= sm & ev[FT].any(1)
    keep |= hem; print('skirt rim faces kept', int(hem.sum()))
if float(E('RIMR', '0')) > 0:
    opn = np.zeros(len(T), bool)
    for p_ in (0, 1, 10, 11):
        sm = part == p_
        se = np.sort(np.r_[FT[sm][:, [0, 1]], FT[sm][:, [1, 2]], FT[sm][:, [2, 0]]], 1); k2, c2 = np.unique(se, axis=0, return_counts=True)
        rvv = np.unique(k2[c2 == 1].ravel())
        rpts = np.array([P[np.flatnonzero(w == x)[0]] for x in rvv])
        opn |= sm & (cKDTree(rpts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < float(E('RIMR', '0')))
    keep |= opn; print('opening faces kept (RIMR)', int(opn.sum()))
cuff = (part == 0) & near(pv(5), CUFF)
collar = (np.isin(part, (0, 1, 11))) & near(pv(3, 4, 7), COLLAR)
graft = (np.isin(part, (0,)) & near(pv(5), GRAFT)) | ((part == 5) & near(pv(0), GRAFT))
sole = (part == 9) & (V[:, :, 1].min(1) < floor + SOLE)
_, tp = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lining].ravel()]] = True
strip = ~lining & linp[tp[T]].any(1)
loose = zero & ~lining & ~strip
hsrc = (loose | strip) if E('HALO_STRIP', '0') == '1' else loose
halo = ~lining & (mat == 0) & (near(np.unique(T[hsrc].ravel()), HALO) if hsrc.any() else False)
# beard contact (the beard gate's set: face-shell faces below the mouth, in front, above the collar)
beard_f = (part == 3) & (C[:, 1] < MOUTH_Y) & (C[:, 2] > -0.02)
beard = (mat == 0) & ~lining & (part != 2) & near(np.unique(T[beard_f].ravel()), BEARD_R)
keep |= cuff | collar | graft | sole | strip | loose | halo | beard
print('hair', int(hair.sum()), 'hairline', int(hl.sum()), 'cuff', int(cuff.sum()), 'collar', int(collar.sum()), 'graft', int(graft.sum()),
      'soles', int(sole.sum()), 'strips', int(strip.sum()), 'loose', int(loose.sum()), 'halo', int((halo & ~strip & ~loose).sum()),
      'beard faces', int(beard_f.sum()), 'beard contact', int(beard.sum()))
if E('SHOULDER', '0') == '1':
    shv = np.array([('Clavicle' in x or 'UpperArm' in x) for x in dv])
    sh = np.isin(part, (0, 11)) & ~lining & shv[T].any(1)
    print('shoulder faces kept', int((sh & ~keep).sum())); keep |= sh
if E('PANEL', '') :
    x0, y0, y1, z0 = map(float, E('PANEL', '').split(','))
    pn = (part == 0) & ~lining & (np.abs(C[:, 0]) < x0) & (C[:, 1] > y0) & (C[:, 1] < y1) & (C[:, 2] > z0)
    print('front panel faces kept', int((pn & ~keep).sum())); keep |= pn
if float(E('DEV', '0')) > 0:
    Nn = np.concatenate([D[k]['N'] for k in PR]).astype(np.float64); Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
    fnm = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); fnm /= np.maximum(np.linalg.norm(fnm, axis=1, keepdims=True), 1e-12)
    dv_ = (np.einsum('fkc,fc->fk', Nn[T], fnm).min(1) < np.cos(np.radians(float(E('DEV', '0'))))) & (mat == 0) & ~lining
    for _ in range(int(E('DEV_RING', '1'))):
        fv = np.zeros(n, bool); fv[w[T[dv_].ravel()]] = True
        dv_ = (mat == 0) & ~lining & fv[w[T]].any(1)
    print('fold faces kept', int((dv_ & ~keep).sum())); keep |= dv_
if E('TIPS', '0') == '1':
    tipv = np.array([x.endswith('3') and any(h in x for h in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in dv])
    tips = (part == 5) & tipv[T].any(1)
    print('fingertip faces kept', int((tips & ~keep).sum())); keep |= tips
if E('HANDS', ''):
    hc = np.load(HERE / 'work' / E('HANDS', '')).astype(bool) & ~lining
    print('hand contact faces kept', int((hc & ~keep).sum())); keep |= hc
for x in [s for s in E('EXTRA', '').split(',') if s]:
    ex = np.load(HERE / x).astype(bool) & ~lining
    print('extra', x, int((ex & ~keep).sum())); keep |= ex
group = np.zeros(len(T), int)
group[part == 5] = 1; group[part == 1] = 3; group[part == 4] = 6; group[part == 9] = 4; group[part == 10] = 5; group[part == 11] = int(E('YOKE_G', '0'))
group[keep] = 0
NAMES = ['tunic', 'trousers', 'small', 'face shell', 'scalp', 'hands', '-', 'collar', '-', 'boots', 'skirt', 'yoke']
for p_ in range(12):
    s = part == p_
    if not s.any():
        continue
    print(f'part {p_} {NAMES[p_]:10s} {s.sum():5d} lining {int((s & lining).sum()):4d} lined {int((s & lined).sum()):4d} '
          f'keep {int((s & keep & ~lining).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} groups',
          {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
prot = keep | (lining & keep[np.maximum(pair, 0)]) | (lining & (pair < 0))
free = int((~keep & ~lining).sum())
print('TOTAL protected', int(prot.sum()), f'({prot.mean() * 100:.1f} %)', 'free', free, 'of', len(T),
      f'-> 15 % of LOD0 ({0.15 * len(T):.0f}) is {0.15 * len(T) / max(free, 1) * 100:.0f} % of the free part')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined & ~lining, part=part,
         mat=mat, pair=pair, beard_f=beard_f)
from set_view import views  # noqa: E402
COL = {0: (150, 150, 150), 1: (40, 200, 40), 2: (240, 140, 30), 3: (220, 210, 60), 4: (60, 200, 220), 6: (205, 160, 120)}
rgb = np.array([COL.get(int(x), (90, 90, 200)) for x in group]); rgb[keep] = (220, 40, 40)
vis = ~lining
views(P, T[vis & (mat == 0)], rgb[vis & (mat == 0)], (-0.8, 0.8, -0.01, 1.6), HERE / 'review' / f'sets_{tag}_body.png', size=520)
hh = vis & (mat == 1) & (np.abs(C[:, 0]) < 0.3)
views(P, T[hh], rgb[hh], (-0.2, 0.2, 1.40, 1.80), HERE / 'review' / f'sets_{tag}_head.png', size=420)
hd = vis & (mat == 1) & (np.abs(C[:, 0]) >= 0.3)
views(P, T[hd], rgb[hd], (-0.9, 0.9, 0.85, 1.2), HERE / 'review' / f'sets_{tag}_hands.png', size=520)
