#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantF5_B then PeasantF5Head) for mpqem.py,
written to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat). PeasantF5 parts (../mm9_peasantf5_claude
uv_tex2.npz): 0 head (face skin, neck seam, hair under the coif, eyeballs), 1 coif, 2 dress (bodice, blouse, puffed sleeves,
standing collar), 3 skirt + apron, 4 legs (shins + shoes inside the skirt), 5 arms (bare arm shells), 6 hands (MPFB, with the
3.5 cm stub inside the forearm), 7 bracelets (procedural rings over the arm/hand junction), 8 ornaments (brooches),
9 buckle, 10 skirt lining (4 mm inside, own chart).
Keep exactly (REDUCTION_BRIEF_20261104 relaxed set for townsfolk, face exact; the MPFB hand graft is reused by other bodies):
- the whole head part (face skin, ears, neck seam, eyes: the head primitive);
- coif faces within COIFEDGE m of a head-part vertex (the face/coif border); dress faces within COLLAR m of a head vertex;
- the hand-graft junction: hand faces whose dominant joint is not a hand/finger joint (the stub on the forearm) and hand,
  arm faces within JUNC m of a bracelet vertex (the bracelet covers the joint); arm faces within CUFF m of a dress vertex
  (the arm leaving the puffed sleeve);
- soles (leg faces below floor + SOLE); ornaments, buckle and connected pieces up to SMALL faces;
- the bracelets (BRACE=keep, default) or group 8 (BRACE=cut, ratio via MP_GROUPS 8:..);
- the skirt lining (LINING=keep, default) or group 6 (LINING=cut).
- SLEEVE=<m>: dress faces beyond |x| SLEEVE m (the puffed sleeves) stay exact.
Shared with PeasantF6 (mm9_peasantf6_reduce_claude, set f; F6 is this body with a new head, hair, braid and ears):
- STUB=<m>: arm faces within STUB m of a hand-stub vertex (the bare forearm over the 3.5 cm stub; F6 c60 showed stub vertices
  through a cut sleeve at rest);
- HEM / WAIST=<m>: skirt faces reaching below floor + HEM m or within WAIST m of the skirt's top (F6: the kept lining's hem rim came
  23 mm out of a cut skirt in Running);
- LPROBE=<tag>:<m>: skirt faces within <m> of the lining vertices work/lining_probe_<tag>.npy lists (lining_probe.py: pushed out of
  the cut skirt more than 1.5 mm beyond the installed in some clip; b55 Running 2.3 -> 7.4 mm at the hip);
- ARMC=1: dress/skirt faces within 1.5 cm of an arm, hand or bracelet vertex in any clip at 10 Hz (scripts/arm_contact.py).
Groups: 1 hand + fingers (seam slides), 2 coif, 3 skirt, 4 shoes (below SHOE m), 5 arm skin, 6 lining, 7 hidden shins,
8 bracelets; 0 = dress (the ladder ratio).  Usage: make_sets_pf5.py <tag>"""
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
COIFEDGE = float(E('COIFEDGE', '0.008')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.01'))
JUNC = float(E('JUNC', '0.012')); SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '80'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf5.glb', 'PeasantF5')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']
PR = ['PeasantF5_B', 'PeasantF5Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
keep = part == 0
coif_edge = (part == 1) & near(pv(0), COIFEDGE)
collar = (part == 2) & near(pv(0), COLLAR)
stub = (part == 6) & ~handj[joint]
junc = np.isin(part, (5, 6)) & near(pv(7), JUNC)
cuff = (part == 5) & near(pv(2), CUFF)
sole = (part == 4) & (V[:, :, 1].min(1) < floor + SOLE)
smallp = np.isin(part, (8, 9))
keep |= coif_edge | collar | stub | junc | cuff | sole | smallp
SLV = float(E('SLEEVE', '0'))
sleeve = (part == 2) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
keep |= sleeve
STUB = float(E('STUB', '0'))
wrist = (part == 5) & near(np.unique(T[stub].ravel()), STUB) if STUB > 0 else np.zeros(len(T), bool)
keep |= wrist
HEM = float(E('HEM', '0')); WAIST = float(E('WAIST', '0')); sk = part == 3; ytop = V[sk][:, :, 1].max()
bands = sk & (((V[:, :, 1].min(1) < floor + HEM) if HEM > 0 else False) | ((V[:, :, 1].max(1) > ytop - WAIST) if WAIST > 0 else False))
keep |= bands
armc = np.load(HERE / 'work' / 'arm_contact.npy') if E('ARMC', '0') == '1' else np.zeros(len(T), bool)
keep |= armc
LP = E('LPROBE', '')
if LP:
    tg, r = LP.split(':'); lp = np.load(HERE / 'work' / f'lining_probe_{tg}.npy')
    lpk = sk & (cKDTree(lp).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < float(r))
    print('skirt round pushed-out lining', int((lpk & ~bands & ~armc).sum())); keep |= lpk
print('wrist (arm over the stub)', int((wrist & ~junc & ~cuff).sum()), 'skirt hem + waist bands', int(bands.sum()),
      'arm contact', int((armc & ~collar & ~bands).sum()))
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')
if E('BRACE', 'keep') == 'keep':
    keep |= part == 7
if E('LINING', 'keep') == 'keep':
    keep |= part == 10
group = np.zeros(len(T), int)
group[(part == 6) & handj[joint]] = 1; group[part == 5] = 5
group[part == 1] = 2; group[part == 3] = 3; group[part == 10] = 6; group[part == 7] = 8
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == 4) & low] = 4; group[(part == 4) & ~low] = 7
group[keep] = 0
names = g['names']
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_} {names[p_]:9s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('coif edge', int(coif_edge.sum()), 'collar', int(collar.sum()), 'stub', int(stub.sum()), 'junction', int((junc & ~stub).sum()),
      'cuff', int(cuff.sum()), 'soles', int(sole.sum()), 'sleeves', int(sleeve.sum()), 'small', int((small & ~smallp & (part != 0)).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(T), bool),
         lined=np.zeros(len(T), bool), part=part, mat=g['mat'])
