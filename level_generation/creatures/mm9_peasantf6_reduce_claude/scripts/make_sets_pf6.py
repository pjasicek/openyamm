#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantF6_A then PeasantF6Head) for mpqem.py,
written to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat). PeasantF6 parts (glb_parts.py): 0 head (face skin,
neck, scalp, eyes, teeth, mouth backing), 1 dress, 2 skirt, 3 legs, 4 arms, 5 hands (MPFB), 6 bracelets, 7 buckle, 8 lining,
9 hair (bob shell + rim strip), 10 ears, 11 braid.
Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact):
- the whole head part (face skin, neck seam, scalp, eyes, teeth, mouth backing), both elf ears, the buckle, the body lining
  (part 8) and every other 'inner' face (collar-band lining, rim strips of the arm tops and hand stubs);
- the hair's rim: hair faces within HAIRRIM m of a head vertex (lower edge tucked onto the skull + the rim strip), hair faces
  within EARR m of an ear vertex (thinned round the ear roots), hair faces within BRAIDR m of a braid vertex (braid root);
- the braid root: braid faces within BROOT m of a hair vertex;
- the collar band's outer dress faces (lined 3 mm in at the build);
- the collar: dress faces within COLLAR m of a head vertex; the sleeve ends: dress faces within CUFF m of an arm/hand vertex;
  dress faces within HW m of a braid vertex (the braid's clearance over the back);
- soles: leg faces below floor + SOLE; connected pieces of up to SMALL faces;
- STUB > 0: the hand's forearm stub and the arm faces within STUB m of it (set d);
- HEM / WAIST > 0: skirt faces within HEM m of the floor or WAIST m of the skirt's top (set e);
- ARMC=1: dress/skirt faces the arms touch in any clip (work/arm_contact.npy, set f);
- SLEEVE > 0: dress faces beyond |x| SLEEVE m (the puff sleeves); BRACELET=keep (default) or a group ratio via group 9.
Groups: 1 hand + fingers (seam slides), 2 hair, 3 skirt, 4 shoes (below SHOE m), 5 arm skin, 7 hidden legs (inside the
skirt), 8 braid, 9 bracelets; 0 = dress (the ladder ratio).
Usage: make_sets_pf6.py <tag>"""
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
HAIRRIM = float(E('HAIRRIM', '0.0035')); EARR = float(E('EARR', '0.01')); BRAIDR = float(E('BRAIDR', '0.015'))
BROOT = float(E('BROOT', '0.01')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.012'))
HW = float(E('HW', '0.025')); SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '40'))
SLV = float(E('SLEEVE', '0'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf6.glb', 'PeasantF6')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; inner = g['inner']
PR = ['PeasantF6_A', 'PeasantF6Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = np.isin(part, (0, 7, 8, 10)) | inner
hair_rim = (part == 9) & near(pv(0), HAIRRIM); hair_ear = (part == 9) & near(pv(10), EARR)
hair_braid = (part == 9) & near(pv(11), BRAIDR); braid_root = (part == 11) & near(pv(9), BROOT)
collar = (part == 1) & near(pv(0), COLLAR); cuff = (part == 1) & near(pv(4, 5), CUFF)
under = (part == 1) & near(pv(11), HW) if HW > 0 else np.zeros(len(T), bool)
sole = (part == 3) & (V[:, :, 1].min(1) < floor + SOLE)
sleeve = (part == 1) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
# the collar band's outer dress faces (line_rims.py lined 278 dress faces 3 mm in; the kept lining must stay under them)
iv = np.unique(T[inner & (part == 1)].ravel())
lined = (part == 1) & ~inner & (cKDTree(P[iv]).query(V.reshape(-1, 3))[0].reshape(-1, 3).max(1) < 0.0035)
keep |= hair_rim | hair_ear | hair_braid | braid_root | collar | cuff | under | sole | sleeve | lined
# the wrist (set d, STUB=0.02): the MPFB hand's forearm stub (hand faces dominated by a Forearm joint) and the arm (painted
# sleeve) faces within STUB m of a stub vertex stay exact; c60 cut the sleeve over the stub at 0.45 and 2 stub vertices per side
# came through it at rest (dark wedges above both cuffs in the close-ups)
STUB = float(E('STUB', '0'))
stub = (part == 5) & np.array(['Forearm' in str(jn[j]) for j in joint])
wrist = (stub | ((part == 4) & near(np.unique(T[stub].ravel()), STUB))) if STUB > 0 else np.zeros(len(T), bool)
keep |= wrist; print('wrist (stub + sleeve over it)', int(wrist.sum()))
# the skirt's hem and waist bands (set e, HEM=0.1, WAIST=0.03): skirt faces reaching below floor + HEM m or within WAIST m of
# the skirt's top; c60 cut them and the kept lining's hem rim came 23 mm out of the skirt in Running (installed 4.1 mm)
HEM = float(E('HEM', '0')); WAIST = float(E('WAIST', '0'))
sk = part == 2; ytop = V[sk][:, :, 1].max()
bands = sk & (((V[:, :, 1].min(1) < floor + HEM) if HEM > 0 else False) | ((V[:, :, 1].max(1) > ytop - WAIST) if WAIST > 0 else False))
keep |= bands; print('skirt hem + waist bands', int(bands.sum()))
# arm contact (set f, ARMC=1): dress/skirt faces within 1.5 cm of an arm, hand or bracelet vertex in any pose of any clip at
# 10 Hz (arm_contact.py); e61 cut the chest under the R forearm in Cower frame 0 (forearm 1.0 -> 1.4 cm into the body)
armc = np.load(HERE / 'work' / 'arm_contact.npy') if E('ARMC', '0') == '1' else np.zeros(len(T), bool)
print('arm contact (new keeps)', int((armc & ~keep).sum())); keep |= armc
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
if E('BRACELET', 'keep') == 'keep':
    keep |= part == 6
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 5) & handj[joint]] = 1; group[(part == 5) & ~handj[joint]] = 5; group[part == 4] = 5
group[part == 9] = 2; group[part == 2] = 3; group[part == 11] = 8; group[part == 6] = 9
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == 3) & low] = 4; group[(part == 3) & ~low] = 7
group[keep] = 0
names = g['names']
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {names[p_]:9s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('hair rim', int(hair_rim.sum()), 'hair-ear', int(hair_ear.sum()), 'hair-braid', int(hair_braid.sum()), 'braid root',
      int(braid_root.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'under braid', int(under.sum()),
      'soles', int(sole.sum()), 'lined collar', int(lined.sum()), 'sleeves', int(sleeve.sum()), 'small', int(small.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(T), bool),
         lined=np.zeros(len(T), bool), part=part, mat=g['mat'])
