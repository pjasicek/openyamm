#!/usr/bin/env python3
"""Annud copy (2026-11-05) of PeasantDM2's make_sets_dm2.py: head shell exact except the scalp/back of the head under the
hair (head_survey.py), hairline exact, legs group = faces of the floor component below LEG_Y0 (the rest of it, the tunic skirt,
at the ladder ratio). PeasantDM2 docstring: PeasantDM2 copy (2026-11-05) of the Dwarf boy's make_sets_dboy.py: legs = boots and trousers (components reaching below
LEG_Y0); head part split into the exact face (FACE window as DM4's make_sets_dm4.py, dilated RING rings; ears, eye/cheek plates and
every one-texel/zero-UV head face; shell faces within NECK_D of the body = neck seam and the beard's torso contact) and the cut
shell: group 6 scalp/back of head (above FACE_Y0), group 7 beard (below FACE_Y0); cuff: tunic faces within CUFF of a hand vertex.
Dwarf boy docstring follows. Keep / group sets per installed GLB LOD0 face (file primitive order: Annud body, AnnudHead) for mpqem.py ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat). Parts by welded connected component (scripts/analyze.py):
body prim: 0 tunic (tunic, sleeves, bare Meshy forearms, collar), 1 legs (trousers + boots, two pieces), 2 small pieces (buttons,
detached sleeve-twin patches); head prim: 3 head (face skin, ears, eyes, neck cap, mouth fill: one piece), 4 hair (three bob
shells), 5 hands (two MPFB hand grafts). Linings from work/twins.npz (twins.py): paired one-texel linings are dropped from the cut
and re-emitted by mpqem.py from the surviving lined faces.
Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact):
- the head part; small pieces (<= SMALL faces) that are not paired linings;
- the collar: tunic faces within COLLAR m of a head-part vertex (neck seam);
- the graft junction: body faces within GRAFT m of a hand vertex and hand faces within GRAFT m of a body vertex (the painted
  wrist band over the seam);
- soles: leg faces below floor + SOLE;
- every face that is not a paired lining but uses a lining vertex (rim strips joining a rim to its lining), unpaired one-texel
  faces (linings whose twin was not found: clamped offsets) and the outer faces within HALO m of their vertices; lining pairs
  where both sides carry UVs (the rim lining's inner-layer twins) on both sides.
Groups: 1 hands (seam slides), 2 hair, 3 legs, 5 forearm skin (dominant Forearm joint, |x| > FOREARM), 0 = tunic (ladder ratio).
Usage: make_sets_dboy.py <tag>   (env SMALL, COLLAR, GRAFT, SOLE, HALO, FOREARM)"""
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
SMALL = int(E('SMALL', '80')); COLLAR = float(E('COLLAR', '0.01')); GRAFT = float(E('GRAFT', '0.015'))
SOLE = float(E('SOLE', '0.012')); HALO = float(E('HALO', '0.006')); FOREARM = float(E('FOREARM', '9'))
LEG_Y0 = float(E('LEG_Y0', '0.50')); CUFF = float(E('CUFF', '0.04')); NECK_D = float(E('NECK_D', '0.02'))
FACE_X, FACE_Y0, FACE_Y1, FACE_Z = (float(E(k, d)) for k, d in (('FACE_X', '0.075'), ('FACE_Y0', '0.985'), ('FACE_Y1', '1.13'), ('FACE_Z', '0.03')))
RING = int(E('RING', '1'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_annud.glb', 'Annud')
PR = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
assert PR == ['Annud', 'AnnudHead'], PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
tw = np.load(HERE / 'work' / 'twins.npz')
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
mat = np.concatenate([[i] * len(D[k]['T']) for i, k in enumerate(PR)])
zero = np.concatenate([tw[f'zero_{k}'] for k in PR])
lining = tw['lining'].astype(bool); lined = tw['lined'].astype(bool)
if E('TW2', '0') == '1':      # PeasantDM2: loose linings mapped by vertex (twins.py second pass) are re-emitted as well
    lining |= tw['lining2'].astype(bool); lined |= tw['lined2'].astype(bool)
pair = np.concatenate([np.where(tw[f'pair_{k}'] >= 0, tw[f'pair_{k}'] + (0 if i == 0 else len(D[PR[0]]['T'])), -1)
                       for i, k in enumerate(PR)])
assert len(lining) == len(T)
floor = P[:, 1].min()
V = P[T]
# components welded by position, per primitive
_, w = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True)
w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl, minlength=lab.max() + 1)
acc = np.zeros((len(T), len(jn)))
for c in range(3):
    J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
    for i in range(4):
        np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
dj = acc.argmax(1); djn = np.array(jn)[dj]
part = -np.ones(len(T), int)
for cmp in np.unique(fl):
    m = fl == cmp; k = int(mat[m][0]); cen = V[m].reshape(-1, 3)
    names = djn[m]
    if k == 0:
        if cnt[cmp] <= SMALL or (m.sum() < 300 and not (cen[:, 1].min() < 0.05)):
            part[m] = 2
        elif cen[:, 1].min() < LEG_Y0:
            part[m] = 1
        else:
            part[m] = 0
    else:
        if np.mean([('Hand' in x or 'Forearm' in x or any(f in x for f in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))) for x in names]) > 0.5:
            part[m] = 5
        elif m.sum() > 2000 or m.sum() < 300:      # PeasantDM2: the shell, and the ears / eye-cheek plates (own components)
            part[m] = 3
        else:
            part[m] = 4
assert (part >= 0).all()
pv = lambda *ps: np.unique(T[np.isin(part, ps)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
# head part 3 (Annud): the shell (largest head component: face, ears, neck, painted beard, scalp) is exact except the scalp
# and back of the head under the hair (head_survey.py: ray along the face normal meets the hair shell within 5 cm) and the
# back of the skull (z < BACK_Z above BACK_Y); the front hairline (z > HAIRLINE_Z), the ears and RING rings round every kept
# shell face stay exact
hm = (part == 3)
_, hc = np.unique(fl[hm], return_counts=True); shell_c = np.unique(fl[hm])[hc.argmax()]
shell = hm & (fl == shell_c)
C = V.mean(1)
hs = np.load(HERE / 'work' / 'head_survey.npz'); nb = int((mat == 0).sum())
under = np.zeros(len(T), bool); under[nb:] = hs['under']
BACK_Z, BACK_Y, HAIRLINE_Z = (float(E(k, d)) for k, d in (('BACK_Z', '-0.02'), ('BACK_Y', '1.55'), ('HAIRLINE_Z', '0.05')))
ear = shell & (np.abs(C[:, 0]) > float(E('EAR_X', '0.068'))) & (C[:, 1] > 1.56) & (C[:, 1] < 1.72) & (C[:, 2] > -0.05)
cutz = shell & (under | ((C[:, 2] < BACK_Z) & (C[:, 1] > BACK_Y))) & ~ear & ~(C[:, 2] > HAIRLINE_Z)
win = shell & ~cutz
for _ in range(RING):
    wv = np.zeros(len(P), bool); wv[T[win].ravel()] = True
    wp = np.zeros(w.max() + 1, bool); wp[w[wv]] = True
    win = shell & wp[w[T]].any(1)
headzero = hm & zero
neck = shell & near(pv(0, 1, 2), NECK_D)
keep = (hm & ~shell) | win | headzero | neck | ((part == 2) & ~lining)
if E('CUFF_HAND', '0') == '1':      # Annud set d: the cuff measured from the hand's wrist (Hand/finger-dominated vertices), not
    # from the whole hand piece, whose forearm stub runs up inside the fitted sleeve (CUFF of it covered the whole forearm sleeve)
    Jc_ = np.concatenate([D[k]['J'] for k in PR]); Wc_ = np.concatenate([D[k]['W'] for k in PR])
    dvn = np.array([jn[Jc_[i][Wc_[i].argmax()]] for i in range(len(Jc_))])
    hvx = np.array([any(h in x for h in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in dvn])
    hv5 = np.zeros(len(P), bool); hv5[pv(5)] = True
    cuff = (part == 0) & near(np.flatnonzero(hv5 & hvx), CUFF)
else:
    cuff = (part == 0) & near(pv(5), CUFF)
keep |= cuff
scalp = shell & ~keep; beard = np.zeros(len(T), bool)
print('head shell', int(shell.sum()), 'exact shell', int(win.sum()), 'zero-UV', int(headzero.sum()), 'neck/beard contact',
      int((neck & ~win).sum()), 'scalp free', int(scalp.sum()), 'beard free', int(beard.sum()), 'cuff', int(cuff.sum()))
collar = (part == 0) & near(pv(3), COLLAR)
graft = (np.isin(part, (0,)) & near(pv(5), GRAFT)) | ((part == 5) & near(pv(0), GRAFT))
sole = (part == 1) & (V[:, :, 1].min(1) < floor + SOLE)
linv = np.zeros(len(P), bool); linv[T[lining].ravel()] = True
# by position (seam copies of a lining vertex)
_, tp = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lining].ravel()]] = True
strip = ~lining & linp[tp[T]].any(1)
loose = zero & ~lining & ~strip & (mat == 0)     # Annud: head-set one-texel faces (neck cap, hand stubs) are not linings: no halo
hsrc = (loose | strip) if E('HALO_STRIP', '1') == '1' else loose     # PeasantDM2: rim strips meet locked rim vertices
halo = ~lining & ~(part == 3) & (near(np.unique(T[hsrc].ravel()), HALO) if hsrc.any() else False)
uvpair = (lining & ~zero)
uvpair_both = uvpair.copy(); uvpair_both[pair[uvpair]] = True
keep |= collar | graft | sole | strip | loose | halo | uvpair_both
# set e (SHOULDER=1): tunic faces using a vertex dominated by a clavicle or upper arm stay exact. d50 cut them and the jitter
# gate's shoulder-skin statistic (p95 over those vertices; every remaining vertex moves exactly as installed) went 1.58 -> 2.92
# mm/f2 in Running R (limit 2.0 over MM9): the brief's rule, keep the part exact rather than iterate
if E('SHOULDER', '0') == '1':
    Jc = np.concatenate([D[k]['J'] for k in PR]); Wc = np.concatenate([D[k]['W'] for k in PR])
    dv = np.array([jn[Jc[i][Wc[i].argmax()]] for i in range(len(Jc))])
    shv = np.array([('Clavicle' in x or 'UpperArm' in x) for x in dv])
    shoulder = (part == 0) & ~lining & shv[T].any(1)
    print('shoulder faces kept', int((shoulder & ~keep).sum())); keep |= shoulder
# Annud set c (PeasantM7's FOOT=<m>, FOOT_RING): boot faces with centroid below FOOT, both boots, plus FOOT_RING rings, stay
# exact: b60 changed the toe profile and the vamp seam's shading at close range (review/crop_boot_c4_b60.png)
if float(E('FOOT', '0')) > 0:
    ft = (part == 1) & ~lining & (C[:, 1] < float(E('FOOT', '0')))
    for _ in range(int(E('FOOT_RING', '1'))):
        fv = np.zeros(len(P), bool); fv[T[ft].ravel()] = True
        fp = np.zeros(w.max() + 1, bool); fp[w[fv]] = True
        ft = (part == 1) & ~lining & fp[w[T]].any(1)
    print('foot faces kept', int((ft & ~keep).sum()), 'L', int((ft & ~keep & (C[:, 0] > 0)).sum()), 'R', int((ft & ~keep & (C[:, 0] < 0)).sum())); keep |= ft
# PeasantDM2 set c3 (HANDS=<npy>): faces the hands come within R of in any clip (hand_contact_dm2.py) stay exact: c250 cut
# the beard and tunic under the resting left hand and failed the arm and hand gate in Death (3.7 cm, one frame; installed 0)
if E('HANDS', ''):
    hc = np.load(HERE / 'work' / E('HANDS', '')).astype(bool) & ~lining
    print('hand contact faces kept', int((hc & ~keep).sum())); keep |= hc
# hairline (Annud): hair-shell faces within HAIRLINE m of its open rim stay exact
from collections import Counter
hairf = part == 4; EC = Counter()
for t in FT[hairf]:
    for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        EC[(min(a, b_), max(a, b_))] += 1
rimw = np.array(sorted({x for k_, c_ in EC.items() if c_ == 1 for x in k_}), int)
rimP = np.array([P[np.flatnonzero(w == x)[0]] for x in rimw]) if len(rimw) else np.zeros((0, 3))
hl = hairf & (cKDTree(rimP).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < float(E('HAIRLINE', '0.012'))) if len(rimw) else hairf & False
print('hair rim verts', len(rimw), 'hairline faces kept', int((hl & ~keep).sum())); keep |= hl
# and the hair faces within HAIRSKIN m of the exact (open) skin of the shell: the hairline over the forehead, temples and neck
hs2 = hairf & near(np.unique(T[win & ~cutz].ravel()), float(E('HAIRSKIN', '0.012')))
print('hair faces at the open skin kept', int((hs2 & ~keep).sum())); keep |= hs2
# Annud set d7 (BELTFRONT=1): cloth below the front of the belt (centroid 0.88 < y < 1.02 m, z > 0.10 m) stays exact: d6 cut it
# with the 9 mm guard and the belt-rim lining vertices behind the tassels read 6-14 mm outside it in every clip (lining gate)
if E('BELTFRONT', '0') == '1':
    bf = np.isin(part, (0, 1)) & ~lining & (C[:, 1] > 0.88) & (C[:, 1] < 1.02) & (C[:, 2] > 0.10)
    print('belt-front faces kept', int((bf & ~keep).sum())); keep |= bf
# Annud set d (TIPS=1): every hand face touching a distal finger/thumb vertex (dominant ...3 joint) stays exact: b60/c2/c3 cut
# the R ring fingertip into a dark-ended prism and stretched the L thumbnail at close range (review/hands_guard_compare.png)
if E('TIPS', '0') in ('1', '2'):
    Jt = np.concatenate([D[k]['J'] for k in PR]); Wt_ = np.concatenate([D[k]['W'] for k in PR])
    dt = np.array([jn[Jt[i][Wt_[i].argmax()]] for i in range(len(Jt))])
    tipv = np.array([x.endswith('3') and any(f in x for f in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for x in dt])
    tips = (part == 5) & (tipv[T].all(1) if E('TIPS', '0') == '2' else tipv[T].any(1))     # TIPS=2: all three corners distal
    print('fingertip faces kept', int((tips & ~keep).sum())); keep |= tips
# a kept lined face keeps its lining as is (re-emitted unchanged); a kept lining whose twin is cut is not allowed
keep_lining = lining & keep
lining_cut = lining & ~keep
assert not (lining_cut & keep[np.maximum(pair, 0)] & False).any()
group = np.zeros(len(T), int)
group[part == 5] = 1; group[part == 4] = 2; group[(part == 1) & (V[:, :, 1].max(1) < LEG_Y0)] = 3; group[scalp] = 6
fore = (part == 0) & np.array(['Forearm' in x for x in djn]) & (np.abs(V[:, :, 0]).min(1) > FOREARM)
group[fore] = 5
# Annud set d (STUB=<ratio> used by the caller as group 8): the one-texel forearm stubs of the hand pieces, inside the sleeves
if E('STUB', '0') == '1':
    group[(part == 5) & zero] = 8
group[keep] = 0
NAMES = ['tunic', 'lower', 'small', 'head', 'hair', 'hands']
for p_ in range(6):
    s = part == p_
    print(f'part {p_} {NAMES[p_]:6s} {s.sum():5d} lining {int((s & lining).sum()):5d} lined {int((s & lined).sum()):5d} '
          f'keep {int((s & keep & ~lining).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} groups',
          {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
print('collar', int(collar.sum()), 'graft', int(graft.sum()), 'soles', int(sole.sum()), 'rim strips', int(strip.sum()),
      'loose linings', int(loose.sum()), 'halo', int((halo & ~strip & ~loose).sum()), 'uv-lining pairs', int(uvpair_both.sum()))
prot = keep | (lining & keep[np.maximum(pair, 0)])
print('TOTAL protected (kept + linings of kept faces)', int(prot.sum()), f'({prot.mean() * 100:.1f} %)', 'free', int((~keep & ~lining).sum()),
      'cut linings', int((lining & ~keep[np.maximum(pair, 0)]).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined & ~lining, part=part,
         mat=mat, pair=pair)
# set views (review/sets_<tag>_{body,head,hands}.png): grey tunic cut at the ladder ratio, red kept, green hands, orange hair,
# yellow legs, tan scalp, cyan beard; linings hidden
from set_view import views  # noqa: E402
COL = {0: (150, 150, 150), 1: (40, 200, 40), 2: (240, 140, 30), 3: (220, 210, 60), 5: (90, 90, 200), 6: (205, 160, 120), 7: (60, 200, 220), 8: (200, 60, 200)}
rgb = np.array([COL[int(x)] for x in group]); rgb[keep] = (220, 40, 40)
vis = ~lining
Cc = V.mean(1)
views(P, T[vis & (mat == 0)], rgb[vis & (mat == 0)], (-0.7, 0.7, -0.01, 1.6), HERE / 'review' / f'sets_{tag}_body.png', size=520)
hh = vis & (mat == 1) & (np.abs(Cc[:, 0]) < 0.3)
views(P, T[hh], rgb[hh], (-0.15, 0.15, 1.42, 1.82), HERE / 'review' / f'sets_{tag}_head.png', size=420)
hd = vis & (mat == 1) & (np.abs(Cc[:, 0]) >= 0.3)
views(P, T[hd], rgb[hd], (-0.82, 0.82, 0.95, 1.27), HERE / 'review' / f'sets_{tag}_hands.png', size=520)
