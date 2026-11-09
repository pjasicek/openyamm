#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantM2 (limbs), Pm2Torso_A, Pm2Head) for
mpqem.py, written to work/glb_sets_<tag>.npz (keep, group, lining, lined, pair, twin, part, mat).
PeasantM2 parts (clean_pm2 labels): 0 MPFB hands (+ forearm stub), 4 wrist skin (Meshy forearm inside the sleeve), 5 trousers,
6 boots, 1 tunic (bodice + bell sleeves), 7 skirt, 9 belt strap, 10 buckle, 20 face shell (face, scalp, neck, eyes, mouth),
21 hair, 22 lips/eyes (PeasantM2 has no elf ears). Linings: 1 skirt + bell-cuff (3 mm, dark texel), 2 skirt cap, 3 hair (2 mm, the hair's paint), 4 upper
tunic (3 mm, dark texel); every matched lining face is re-emitted by mpqem.py from the twins of its cut outer faces.
Keep exactly (REDUCTION_BRIEF_20261104 relaxed set for prio-2 townsfolk, face exact):
- face shell (20) and ears (22) whole; hair faces within HAIREDGE m of the hair shell's open rim (the hairline);
- collar: tunic faces within COLLAR m of a face-shell vertex (neck seam); cuffs: tunic faces within CUFF m of the tunic's open
  rim near the hands (bell-cuff rim + its two-sided hem); belt strap and buckle whole; skirt cap; soles (boot faces below
  floor + SOLE); connected pieces of up to SMALL faces;
- lining faces without an outer twin face and every face within 1 cm of them; faces round ambiguous twin vertices.
Groups: 1 hand + fingers (seam slides), 5 forearm skin (part 0 forearm-weighted + part 4), 2 hair, 3 skirt, 4 boots,
6 trousers, 0 = tunic (the ladder ratio).
Usage: make_sets_pm2.py <tag>  (env HAIREDGE, COLLAR, CUFF, SOLE, SMALL, EXTRA=<npy of extra keep faces>)"""
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
HAIREDGE = float(E('HAIREDGE', '0.012')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.04'))
SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '80'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm2.glb', 'PeasantM2')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; lin = g['lining']
PR = ['PeasantM2', 'Pm2Torso_A', 'Pm2Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = g['voff']
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda m: np.unique(T[m].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
outer = lin == 0
keep = np.isin(part, (20, 22)) | (lin == 2) | np.isin(part, (9, 10))
collar = (part == 1) & near(pv(part == 20), COLLAR)
# the tunic's open rim near the hands: boundary edges of the outer tunic (welded by position) within 12 cm of a hand vertex
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
tun = np.flatnonzero((part == 1) & outer)
ec = {}
for f in tun:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        e = (min(FT[f, a], FT[f, b]), max(FT[f, a], FT[f, b])); ec[e] = ec.get(e, 0) + 1
rimw = np.unique([x for e, c in ec.items() if c == 1 for x in e])
rep = np.zeros(w.max() + 1, np.int64); rep[w] = np.arange(len(w))
rimP = P[rep[rimw]]
handP = P[pv(part == 0)]
rim_cuff = rimP[cKDTree(handP).query(rimP)[0] < 0.12]
print('tunic open rim verts', len(rimw), 'near hands', len(rim_cuff))
cuff = (part == 1) & (cKDTree(rim_cuff).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < CUFF) if len(rim_cuff) else np.zeros(len(T), bool)
# the hairline: hair faces within HAIREDGE of the hair shell's open rim (the forehead, temple and nape edge on the skin)
hf = np.flatnonzero((part == 21) & outer); ec = {}
for f in hf:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        e = (min(FT[f, a], FT[f, b]), max(FT[f, a], FT[f, b])); ec[e] = ec.get(e, 0) + 1
hrim = P[rep[np.unique([x for e, c in ec.items() if c == 1 for x in e])]]
print('hair rim verts', len(hrim))
hairline = (part == 21) & outer & (cKDTree(hrim).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HAIREDGE)
sole = (part == 6) & (V[:, :, 1].min(1) < floor + SOLE)
keep |= hairline | collar | cuff | sole
# lining without an outer face: keep it and every face within 1 cm (centre-seam skirt and collar faces)
um = g['unmatched']
if um.any():
    cu = P[T[um]].mean(1); keep |= cKDTree(cu).query(V.mean(1))[0] < 0.01
amb = np.flatnonzero(g['ambig'])
if len(amb):
    keep |= np.isin(w[T], w[amb]).any(1)
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]; n = w.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:14]}')
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); keep |= ex; print('extra keep', x, int(ex.sum()))
lining = (lin != 0) & (lin != 2) & ~um
lined = g['lined'].copy()
# a kept outer face keeps its lining face as it is (paired); a kept lining face (unmatched) is not re-emitted
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 0) & handj[joint]] = 1; group[((part == 0) & ~handj[joint]) | (part == 4)] = 5
group[part == 21] = 2; group[part == 7] = 3; group[part == 6] = 4; group[part == 5] = 6
group[keep] = 0
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {s.sum():5d} keep {int((s & keep).sum()):5d} lining {int((s & lining).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} groups',
          {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
print('hairline', int(hairline.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'soles', int(sole.sum()),
      'small', int((small & ~np.isin(part, (20, 22))).sum()), 'unmatched-near', int(um.sum()), 'ambig verts', len(amb))
kl = keep & ~lining
# protected = kept outer faces + the lining faces paired to kept lined faces (re-emitted unchanged)
pk = int(kl.sum()) + int((lined & keep).sum())
print('TOTAL keep', int(kl.sum()), f'({kl.mean() * 100:.1f} %)', '+ their linings', int((lined & keep).sum()), f'= protected {pk} ({pk / len(T) * 100:.1f} %)',
      'free', int((~keep & ~lining).sum()), 'lining re-emitted', int(lining.sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, pair=g['pair'],
         twin=g['twin'], part=part, mat=g['mat'])
