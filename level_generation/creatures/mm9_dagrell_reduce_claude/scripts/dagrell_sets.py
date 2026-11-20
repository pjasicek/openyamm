#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Dagrell LOD0 (one primitive, Dagrell_A) for mpqem.py: work/glb_sets_<tag>.npz.
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104), Dagrell reading (a skeleton of ~136 rigid bone pieces):
- exact: every head piece (faces dominated by Xheadpiv / Xjawbase / Xjawpiv / Xnose: skull with eye sockets, mandible, teeth,
  head spikes) and the neck piece XneckB (the neck seam); tiny pieces (<= SMALL faces: teeth, spurs); thin spikes (pieces
  under THIN_N faces whose shortest extent is < THIN of the longest); claws and toes (faces dominated by a digit bone
  Xfin*/Xfmid*/Xtoe*); soles (faces within SOLE of the floor, glTF +Y up);
- group 2 (set b, CRANIUM_Z): the back of the skull and head pieces behind CRANIUM_Z;
- group 0: everything else (spine, ribs, pelvis, limb bones, feet, tail vertebrae and blade).
Usage: dagrell_sets.py <tag>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
SMALL = int(E('SMALL', '20')); THIN = float(E('THIN', '0.3')); THIN_N = int(E('THIN_N', '60')); SOLE = float(E('SOLE', '0.02'))
tag = sys.argv[1]
doc, b = gb.read(HERE / 'before' / 'mm9_dagrell.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Dagrell' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
nF = len(T)
_, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
dom = fw.argmax(1)
head = np.isin(dom, [joints.index(n) for n in ('Xheadpiv', 'Xjawbase', 'Xjawpiv', 'Xnose', 'XneckB')])
small = cnt[fl] <= SMALL
thin = np.zeros(nF, bool)
for c in np.unique(fl):
    f = fl == c; v = np.unique(T[f]); ext = np.sort(np.ptp(P[v], 0))
    if ext[0] / max(ext[2], 1e-9) < THIN and cnt[c] < THIN_N:
        thin |= f
digit = np.array([joints[d].startswith(('Xfin', 'Xfmid', 'Xtoe')) for d in dom])
sole = P[T][:, :, 1].min(1) < P[:, 1].min() + SOLE
keep = head | small | thin | digit | sole
group = np.zeros(nF, int)
CRANIUM_Z = float(E('CRANIUM_Z', '0'))   # set b: skull faces behind z (head forward is +z; nose at 1.017, head pivot 0.58) -> group 2
if CRANIUM_Z > 0:
    cran = head & ~small & ~thin & (P[T].mean(1)[:, 2] < CRANIUM_Z) & (dom != joints.index('XneckB'))
    keep &= ~cran; group[cran] = 2; print('cranium (group 2)', int(cran.sum()))
print(f'faces {nF}: head+neck {int(head.sum())}, small {int(small.sum())}, thin {int(thin.sum())}, digits {int(digit.sum())}, '
      f'soles {int(sole.sum())}')
print(f'group 0: free {int((~keep).sum())}')
print(f'protected share {keep.sum() / nF * 100:.1f} % ({int(keep.sum())} of {nF})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(nF, bool), lined=np.zeros(nF, bool),
         head=head, small=small, thin=thin, digit=digit, sole=sole)
