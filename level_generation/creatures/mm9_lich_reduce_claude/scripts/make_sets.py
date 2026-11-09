#!/usr/bin/env python3
"""Keep / group / lining sets per installed LOD0 face (Lich_A then LichHead_A) for mpqem.py, from work/glb_parts.npz.
Parts (prep_v2): 1 pants, 2 cloak (sleeves, cape, hood), 3/10 hands, 4/7 boots, 6 belt, 8 robe, 12 neck bones, 14 medallion,
30 skull (LichHead_A), 40/41/42 linings of hood / robe / boot flares (prep_v2's 4 mm inner copies, reversed).
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104):
- exact: the skull primitive (mpqem KEPT_PRIMS), neck bones (12) and medallion (14), soles (boot faces within SOLE of the
  floor), the hand junction (hand faces on the wrist opening + JRINGS rings), body faces the hands rest on and hand faces
  touching the other hand (work/hand_contact.npy), connected pieces of up to SMALL faces, the belt if BELT=keep;
- linings (40-42) are not cut: mpqem re-emits them from the surviving lined outer faces' twins;
- groups (own ratio, MP_GROUPS): 1 hands, 2 hood (cloak faces prep_v2 lined, above HOOD_Z in Blender z), 3 robe, 4 boots above
  the soles, 5 belt; 0 = sleeves and cape, pants (the ladder ratio).
Usage: make_sets.py <tag>  -> work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat)"""
import os, sys
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
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.03')); JRINGS = int(E('JRINGS', '2'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_lich.glb', 'Lich')
g = np.load(HERE / 'work' / 'glb_parts.npz'); f = np.load(HERE / 'work' / 'final_parts.npz')
part, mat = g['part'], g['mat']
A = D['Lich_A']; P, T = A['P'], A['T']; nA = len(T); n = len(part)
pa = part[:nA]
keep = np.zeros(n, bool); keep[nA:] = True
keep[:nA] |= np.isin(pa, (12, 14))
lining = np.zeros(n, bool); lining[:nA] = pa >= 40
# welded topology on Lich_A (by position)
_, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
floor = P[:, 1].min()
sole = np.isin(pa, (4, 7)) & (P[T][:, :, 1].min(1) < floor + SOLE); keep[:nA] |= sole
hand = np.isin(pa, (3, 10))
ed = np.sort(np.vstack([FT[hand][:, [0, 1]], FT[hand][:, [1, 2]], FT[hand][:, [2, 0]]]), 1)
u, c = np.unique(ed, axis=0, return_counts=True)
other = np.zeros(nW, bool); other[u[c == 1].ravel()] = True; other[FT[~hand].ravel()] = True
junc = hand & other[FT].any(1)
for _ in range(JRINGS):
    hot = np.zeros(nW, bool); hot[FT[junc].ravel()] = True; junc |= hand & hot[FT].any(1)
keep[:nA] |= junc
hc = np.load(HERE / 'work' / 'hand_contact.npy') if E('HAND_CONTACT', '1') == '1' else np.zeros(nA, bool)
keep[:nA] |= hc & (pa < 40)
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = (cnt[fl] <= SMALL) & (pa < 40); keep[:nA] |= small
for p in np.unique(pa):
    s = pa == p; sizes = sorted(np.bincount(fl[s])[np.bincount(fl[s]) > 0].tolist(), reverse=True)
    print(f'  part {p:2d} pieces {sizes[:10]}')
if E('BELT', '') == 'keep':
    keep[:nA] |= pa == 6
# lined outer faces: prep_v2's own rule on the rigged master (hood: cloak faces with min z > 1.5; robe; boot faces min z > 0.5),
# carried to the GLB by the face map of glb_parts (final_parts centroid order = glb face via nearest centroid)
fc_master = f['cen']; zmin = f['co'][f['fv']][:, :, 2].min(1); fpart = f['part']
lined_m = ((fpart == 2) & (zmin > float(E('HOOD_Z', '1.5')))) | (fpart == 8) | (np.isin(fpart, (4, 7)) & (zmin > 0.5))
hood_m = (fpart == 2) & (zmin > float(E('HOOD_Z', '1.5')))
nn = g['src']                                                   # glb face -> master face (glb_parts.py)
lined = lined_m[nn] & ~lining; hood = hood_m[nn]
print('lined', {int(p): int((lined & (part == p)).sum()) for p in np.unique(part[lined])}, 'linings', {int(p): int((part == p).sum()) for p in (40, 41, 42)})
group = np.zeros(n, int)
group[:nA][hand] = 1; group[hood] = 2; group[part == 8] = 3; group[np.isin(part, (4, 7))] = 4; group[part == 6] = 5
group[keep | lining] = 0
for p in np.unique(part):
    s = part == p
    print(f'part {p:2d} {s.sum():6d} keep {int((s & keep).sum()):5d} lining {int((s & lining).sum()):4d} free {int((s & ~keep & ~lining).sum()):5d} lined {int((s & lined).sum()):4d}')
print('soles', int(sole.sum()), 'junction', int(junc.sum()), 'small', int(small.sum()), 'hand contact', int((hc & (pa < 40)).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', n,
      '| groups', {k: int(((group == k) & ~keep & ~lining).sum()) for k in range(6)})
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, part=part, mat=mat)
