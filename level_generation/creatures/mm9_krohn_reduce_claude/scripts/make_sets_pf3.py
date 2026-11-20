#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantF3_B then PeasantF3Head) for mpqem.py,
written straight to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat). PeasantF3 parts: 0 head (face skin, neck,
fringe, eyes, teeth), 1 scarf (hood), 2 dress (bodice, sleeves), 3 skirt, 4 legs (below the knee, inside the skirt), 5 hands
(MPFB arms: upper-arm stub, forearm, hand, fingers), 6 skirt lining (F1's, already decimated to 60 % at the F3 build: not a
twin of the skirt), 7 veil (+ lining + rim), 8 braids.
Keep exactly (REDUCTION_BRIEF_20261104, relaxed set applied to prio-2 townsfolk, face exact):
- the whole head part (face skin, neck seam, eyes, teeth), the veil (thin sheet + lining: shredded by any cut at the build) and the
  braids (tubes already merged 4 rings into 1 at the build);
- the hood edge: hood faces within HOODEDGE m of a head-part vertex (the face/hood border was repainted several times) and
  within VEILR m of a veil vertex (the veil's top row lies 1.5 mm on the hood);
- the collar: dress faces within COLLAR m of a head-part vertex; the sleeve hems: dress faces within CUFF m of an arm vertex;
- soles: leg faces below floor + SOLE; connected pieces of up to SMALL faces;
- the skirt lining (LINING=keep, default) or its own group 6 (LINING=<ratio> via MP_GROUPS 6:..).
Groups: 1 hand + fingers (seam slides), 2 hood, 3 skirt, 4 shoes (below SHOE m), 5 arm skin (upper arm + forearm),
7 hidden legs (above SHOE m, inside the skirt), 6 lining; 0 = dress (the ladder ratio).
- set g (+ SLEEVE=0.15): the short sleeves' dress faces (the arm stub poked through the cut sleeve).
- set e (HW=0.025): dress and hood faces within HW of a veil or braid vertex (the headwear's contact).
Usage: make_sets_pf3.py <tag>"""
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
HOODEDGE = float(E('HOODEDGE', '0.008')); VEILR = float(E('VEILR', '0.015')); COLLAR = float(E('COLLAR', '0.01'))
CUFF = float(E('CUFF', '0.012')); SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '40'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf3.glb', 'PeasantF3')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']
PR = ['PeasantF3_B', 'PeasantF3Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]                                                                     # (F,3,3)
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = np.isin(part, (0, 7, 8))
hood_edge = (part == 1) & near(pv(0), HOODEDGE); hood_veil = (part == 1) & near(pv(7), VEILR)
collar = (part == 2) & near(pv(0), COLLAR); cuff = (part == 2) & near(pv(5), CUFF)
sole = (part == 4) & (V[:, :, 1].min(1) < floor + SOLE)
keep |= hood_edge | hood_veil | collar | cuff | sole
# under the headwear (HW m, set e): dress and hood faces near the veil and braid vertices stay exact, so the headwear's clearance
# over the bodice and shoulders is the installed one (d45 cut them: headwear gate veil 1.3 -> 1.9 cm in Standing, braids 0 -> 0.4 cm
# at rest)
HW = float(E('HW', '0'))
under = np.isin(part, (1, 2)) & near(pv(7, 8), HW) if HW > 0 else np.zeros(len(T), bool)
keep |= under; print('under headwear', int((under & ~(hood_edge | hood_veil | collar)).sum()))
# the short sleeves (set g, SLEEVE=0.15): dress faces beyond |x| SLEEVE m (sleeve_poke_pf1.py's sleeve) stay exact; f50 cut them
# and the MPFB upper-arm stub came 1.8 mm through the R sleeve in Conv1 (17 of 101 frames; installed 0)
SLV = float(E('SLEEVE', '0'))
sleeve = (part == 2) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
keep |= sleeve; print('sleeves', int((sleeve & ~keep_before).sum()) if False else int(sleeve.sum()))
# connected pieces (welded by position, per primitive)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')
lining = part == 6
if E('LINING', 'keep') == 'keep':
    keep |= lining
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 5) & handj[joint]] = 1; group[(part == 5) & ~handj[joint]] = 5
group[part == 1] = 2; group[part == 3] = 3; group[part == 6] = 6
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == 4) & low] = 4; group[(part == 4) & ~low] = 7
group[keep] = 0
names = g['names']
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_} {names[p_]:7s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('hood edge', int(hood_edge.sum()), 'hood under veil', int((hood_veil & ~hood_edge).sum()), 'collar', int(collar.sum()),
      'cuff', int(cuff.sum()), 'soles', int(sole.sum()), 'small', int((small & ~np.isin(part, (0, 7, 8))).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(T), bool),
         lined=np.zeros(len(T), bool), part=part, mat=g['mat'])
