#!/usr/bin/env python3
"""PeasantM8d keep / group sets (Forad's body: the body primitive is one welded piece; the head primitive is one shell of face,
ears, neck, scalp hair and a tunic collar band, plus the ponytail, two ponytail ties and the two MPFB hands). Adapted from
make_sets_m7d.py (PeasantM7d reduction). Per installed GLB LOD0 face (file primitive order PeasantM8d, PeasantM8dHead) ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, pair) for mpqem.py, and review/sets_<tag>_{body,head,hands}.png.
Parts: body prim 0 tunic (dominant Spine/Neck/Clavicle/arm/helper bones), 1 legs (dominant Thigh/Calf/Foot/Toe);
head prim 3 shell (largest component), 4 ponytail (second largest), 2 ties (other small head pieces, kept), 5 hands.
Shell classes from work/head_classes.npz (head_classes.py: texture colour skin / hair / tunic):
- exact: every skin face (face, ears, neck), every hair face in front of FRONT_Z (brows, moustache, forelock, sideburns),
  HRING rings of hair round the skin (the hairline), the tunic collar band in the head material (neck seam); only the scalp
  hair behind it is cut (group 6);
- body: collar (within COLLAR of a head-prim vertex), graft/cuffs (within GRAFT / CUFF of a hand vertex), soles, rim strips,
  loose linings and their halo, hand contact (HANDS npy), optional SHOULDER (Clavicle/UpperArm dominated tunic faces).
Groups: 1 hands, 2 ponytail, 3 legs, 6 scalp hair, 0 tunic (ladder ratio). Usage: make_sets_m8d.py <tag>"""
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
SOLE = float(E('SOLE', '0.012')); HALO = float(E('HALO', '0.006')); FRONT_Z = float(E('FRONT_Z', '0.0'))
HRING = int(E('HRING', '1')); TIES_CUT = E('TIES_CUT', '0') == '1'
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm8d.glb', 'PeasantM8d')
PR = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
assert PR == ['PeasantM8d', 'PeasantM8dHead'], PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
tw = np.load(HERE / 'work' / 'twins.npz'); hcl = np.load(HERE / 'work' / 'head_classes.npz')
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
part[(mat == 0) & legj] = 1; part[(mat == 0) & ~legj] = 0
hcomp = hcl['comp']; hc_ = np.bincount(hcomp); order = np.argsort(-hc_)
HANDN = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm')
comp_head = np.full(len(T), -1); comp_head[nb:] = hcomp
for c in np.unique(hcomp):
    m = (mat == 1) & (comp_head == c)
    if np.mean([any(h in x for h in HANDN) for x in djn[m]]) > 0.5:
        part[m] = 5
    elif c == order[0]:
        part[m] = 3
    elif hc_[c] > 300:
        part[m] = 4
    else:
        part[m] = 2
assert (part >= 0).all()
cls = np.full(len(T), -1); cls[nb:] = hcl['cls']
pv = lambda *ps: np.unique(T[np.isin(part, ps)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
shell = part == 3
hair = shell & (cls == 1)
BACK_Z = float(E('BACK_Z', '-9')); BACK_Y = float(E('BACK_Y', '9'))
# skin-coloured texels inside the scalp hair (darker strands read as skin): treated as hair behind BACK_Z above BACK_Y
hair = hair | (shell & (cls == 0) & (C[:, 2] < BACK_Z) & (C[:, 1] > BACK_Y))
exact_shell = shell & ~(hair & (C[:, 2] <= FRONT_Z))
for _ in range(HRING):         # hairline: hair faces sharing a vertex position with an exact shell face
    ev = np.zeros(n, bool); ev[w[T[exact_shell].ravel()]] = True
    exact_shell |= shell & ev[w[T]].any(1)
scalp = shell & ~exact_shell
keep = exact_shell | ((part == 2) & (not TIES_CUT))
cuff = (part == 0) & near(pv(5), CUFF)
collar = (np.isin(part, (0, 1))) & near(pv(3, 4, 2), COLLAR)
graft = (np.isin(part, (0,)) & near(pv(5), GRAFT)) | ((part == 5) & near(pv(0), GRAFT))
sole = (part == 1) & (V[:, :, 1].min(1) < floor + SOLE)
_, tp = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lining].ravel()]] = True
strip = ~lining & linp[tp[T]].any(1)
loose = zero & ~lining & ~strip
hsrc = (loose | strip) if E('HALO_STRIP', '0') == '1' else loose
halo = ~lining & (mat == 0) & (near(np.unique(T[hsrc].ravel()), HALO) if hsrc.any() else False)
keep |= cuff | collar | graft | sole | strip | loose | halo
print('shell', int(shell.sum()), 'exact', int(exact_shell.sum()), 'scalp free', int(scalp.sum()), 'cuff', int(cuff.sum()),
      'collar', int(collar.sum()), 'graft', int(graft.sum()), 'soles', int(sole.sum()), 'strips', int(strip.sum()), 'loose', int(loose.sum()),
      'halo', int((halo & ~strip & ~loose).sum()))
if E('SHOULDER', '0') == '1':
    shv = np.array([('Clavicle' in x or 'UpperArm' in x) for x in dv])
    sh = (part == 0) & ~lining & shv[T].any(1)
    print('shoulder faces kept', int((sh & ~keep).sum())); keep |= sh
# set c (2026-11-05): b r60 darkened the lower corner of the model's left lapel above the belt (close-up c13: a shading blob where
# the cut cloth stretched the fold's inward vertex normals over larger faces). PANEL=1 keeps the tunic front between the belt
# and the chest (|x| < 0.16, 1.02 < y < 1.40, z > 0.04: both lapels and the panel between); DEV=<deg> keeps body faces with a
# corner normal more than DEV from the face normal (other folds), DEV_RING rings round them.
if E('PANEL', '0') == '1':
    pn = (part == 0) & ~lining & (np.abs(C[:, 0]) < 0.16) & (C[:, 1] > 1.02) & (C[:, 1] < 1.40) & (C[:, 2] > 0.04)
    print('front panel faces kept', int((pn & ~keep).sum())); keep |= pn
if float(E('DEV', '0')) > 0:
    Nn = np.concatenate([D[k]['N'] for k in PR]).astype(np.float64); Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
    fnm = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); fnm /= np.maximum(np.linalg.norm(fnm, axis=1, keepdims=True), 1e-12)
    dv_ = (np.einsum('fkc,fc->fk', Nn[T], fnm).min(1) < np.cos(np.radians(float(E('DEV', '0'))))) & (mat == 0) & ~lining
    for _ in range(int(E('DEV_RING', '1'))):
        fv = np.zeros(n, bool); fv[w[T[dv_].ravel()]] = True
        dv_ = (mat == 0) & ~lining & fv[w[T]].any(1)
    print('fold faces kept', int((dv_ & ~keep).sum())); keep |= dv_
if E('HANDS', ''):
    hc = np.load(HERE / 'work' / E('HANDS', '')).astype(bool) & ~lining
    print('hand contact faces kept', int((hc & ~keep).sum())); keep |= hc
group = np.zeros(len(T), int)
group[part == 5] = 1; group[part == 4] = 2; group[part == 1] = 3; group[scalp] = 6; group[(part == 2) & TIES_CUT] = 2   # TIES_CUT is a Python bool
group[keep] = 0
NAMES = ['tunic', 'legs', 'ties', 'shell', 'ponytail', 'hands']
for p_ in range(6):
    s = part == p_
    print(f'part {p_} {NAMES[p_]:8s} {s.sum():5d} lining {int((s & lining).sum()):4d} lined {int((s & lined).sum()):4d} '
          f'keep {int((s & keep & ~lining).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} groups',
          {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
prot = keep | (lining & keep[np.maximum(pair, 0)]) | (lining & (pair < 0))
print('TOTAL protected', int(prot.sum()), f'({prot.mean() * 100:.1f} %)', 'free', int((~keep & ~lining).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined & ~lining, part=part,
         mat=mat, pair=pair)
from set_view import views  # noqa: E402
COL = {0: (150, 150, 150), 1: (40, 200, 40), 2: (240, 140, 30), 3: (220, 210, 60), 6: (205, 160, 120)}
rgb = np.array([COL.get(int(x), (90, 90, 200)) for x in group]); rgb[keep] = (220, 40, 40)
vis = ~lining
views(P, T[vis & (mat == 0)], rgb[vis & (mat == 0)], (-0.8, 0.8, -0.01, 1.6), HERE / 'review' / f'sets_{tag}_body.png', size=520)
hh = vis & (mat == 1) & (np.abs(C[:, 0]) < 0.3)
views(P, T[hh], rgb[hh], (-0.2, 0.2, 1.40, 1.80), HERE / 'review' / f'sets_{tag}_head.png', size=420)
hd = vis & (mat == 1) & (np.abs(C[:, 0]) >= 0.3)
views(P, T[hd], rgb[hd], (-0.9, 0.9, 1.0, 1.3), HERE / 'review' / f'sets_{tag}_hands.png', size=520)
