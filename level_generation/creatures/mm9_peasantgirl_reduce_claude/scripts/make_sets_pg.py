#!/usr/bin/env python3
"""Keep / group sets per installed elf LOD0 face (work/glb_parts.npz order: PeasantGirl_G1E then PeasantGirlHead) for
mpqem.py -> work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat). The human GLB is the elf minus the ears, so this
one set serves both. Parts: 0 head (face skin, neck to the level seam, eyeballs, scalp), 1 skirt + apron, 2 dress (bodice, vest,
sleeves, bell cuffs and their caps), 3 hair, 4 buttons, 5 legs (shins + shoes), 6 hands (MPFB, 3 cm stub inside the cuff),
7 ears (elf), 8 lining (skirt twin 4 mm in + hem/apron rims + waist cap).
Keep exactly (REDUCTION_BRIEF_20261104, prio-2 relaxed set, face exact):
- head and ears whole; buttons and pieces up to SMALL faces;
- the collar: dress faces within COLLAR m of a head vertex (neck seam); the cuffs: dress faces within CUFF m of a hand vertex
  (bell cuff rim and cap), and the hand-graft junction: hand faces within JUNCTION m of a dress vertex plus the Forearm stub;
- the hairline: hair faces within HAIRLINE m of the hair shell's open edges in front of the ears (z > HAIRZ, tweak_pg's sunk band),
  hair faces within EARR m of an ear vertex (the ears come out through the hair);
- soles: leg faces below floor + SOLE;
- lining faces that are not skirt twins (rims, waist cap) and skirt faces without a twin (work/lining_twins.npz).
Groups: 1 hand + fingers (seam slides), 2 hair, 3 skirt (lining re-emitted from the twins), 4 shoes (below SHOE m), 7 hidden
shins (above SHOE m, inside the skirt); 0 = dress (the ladder ratio). Set option SLEEVE: dress faces beyond |x| SLEEVE kept.
Usage: make_sets_pg.py <tag>"""
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
COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.025')); SOLE = float(E('SOLE', '0.012'))
SHOE = float(E('SHOE', '0.10')); SMALL = int(E('SMALL', '40')); HAIRLINE = float(E('HAIRLINE', '0.015'))
HAIRZ = float(E('HAIRZ', '0.0')); JUNCTION = float(E('JUNCTION', '0.012')); EARR = float(E('EARR', '0.012')); SLV = float(E('SLEEVE', '0'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
jn = g['jnames']; joint = g['joint']
PR = ['PeasantGirl_G1E', 'PeasantGirlHead']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = np.isin(part, (0, 4, 7))
collar = (part == 2) & near(pv(0), COLLAR); cuff = (part == 2) & near(pv(6), CUFF); junction = (part == 6) & near(pv(2), JUNCTION)
# the hand-graft stub (hand faces dominated by a Forearm joint: the 3 cm MPFB stub inside the cuff) stays exact
stub = (part == 6) & np.array(['Forearm' in str(x) for x in jn])[joint]; junction |= stub
sole = (part == 5) & (V[:, :, 1].min(1) < floor + SOLE)
# hair: open edges of the hair shell (welded by position), front ones (z > HAIRZ in glTF: +z is the face's forward side)
hs = np.flatnonzero(part == 3); _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel()
ed = {}
for t in w[T[hs]]:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        k = (min(a, b), max(a, b)); ed[k] = ed.get(k, 0) + 1
bv = np.unique([x for k, c in ed.items() if c == 1 for x in k])
Pw = np.zeros((w.max() + 1, 3)); Pw[w] = P
fwd = np.sign(np.median(P[pv(0)][:, 2] - P[pv(0)][:, 2].mean()) or 1)
front = bv[Pw[bv][:, 2] > HAIRZ] if len(bv) else bv
print('hair open-edge verts', len(bv), 'front (z >', HAIRZ, ')', len(front))
hairline = (part == 3) & (cKDTree(Pw[front]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HAIRLINE) if len(front) else np.zeros(len(T), bool)
earc = (part == 3) & near(pv(7), EARR)
keep |= collar | cuff | junction | sole | hairline | earc
sleeve = (part == 2) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
keep |= sleeve
# connected pieces (welded by position)
FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')
# lining twins (lining_twins.py; body prim face indices = first block)
tw = np.load(HERE / 'work' / 'lining_twins.npz')['twin_face']; nb = len(D[PR[0]]['T'])
twf = np.zeros(len(T), np.int64) - 1; twf[:nb] = tw
lined = (part == 1) & (twf >= 0)
lining = np.zeros(len(T), bool); lining[twf[lined]] = True
keep |= (part == 8) & ~lining                 # rims, waist cap
keep |= (part == 1) & ~lined                  # skirt faces without a twin
# scalp under the hair (set option SCALP=<m>): head-shell faces whose normal ray meets the hair within 4 cm and that lie more than
# SCALP m from the hair shell's open edges (work/scalp_dist.npy, scalp_dist.py) form group 5; the face skin, ears, eyes and neck
# stay exact (none of them is under the hair)
SC = float(E('SCALP', '0'))
scalp = np.zeros(len(T), bool)
if SC > 0:
    sd = np.load(HERE / 'work' / 'scalp_dist.npy'); nb0 = len(D[PR[0]]['T'])
    sel = sd[(sd[:, 1] < 0.04) & (sd[:, 2] > SC), 0].astype(int) + nb0
    scalp[sel] = True; keep[sel] = False
    print('scalp under the hair', int(scalp.sum()))
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[part == 6] = 1; group[part == 3] = 2; group[part == 1] = 3; group[scalp] = 5
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == 5) & low] = 4; group[(part == 5) & ~low] = 7
group[keep] = 0
lined &= ~keep
names = g['names']
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_} {names[p_]:7s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} '
          f'lining {int((s & lining).sum())} groups', {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
print('collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'junction', int(junction.sum()), 'soles', int(sole.sum()),
      'hairline', int(hairline.sum()), 'ear clearance', int((earc & ~hairline).sum()), 'sleeves', int(sleeve.sum()),
      'small', int((small & ~np.isin(part, (0, 4, 7))).sum()))
hum = part != 7
print('TOTAL keep (elf)', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining twins', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', len(T))
print('TOTAL keep (human)', int((keep & hum).sum()), f'({(keep & hum).sum() / hum.sum() * 100:.1f} %)', 'of', int(hum.sum()))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, part=part, mat=g['mat'])
