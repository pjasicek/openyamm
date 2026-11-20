#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantF1_B then PeasantF1Head) for mpqem.py,
written to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim). PeasantF1 parts (uv_tex2.npz):
0 head (face skin, neck, eyes, teeth), 1 scarf (hood), 2 dress (bodice, sleeves, lacing), 3 skirt, 4 legs (below the knee,
inside the skirt), 5 hands (MPFB arms: upper-arm stub, forearm, hand, fingers), 6 lining (skirt lining + hem rim).

The skirt lining (assemble_pf1.lining) is the skirt's exact twin: lining face k = skirt face k reversed, every vertex 4 mm in
along the skirt's vertex normal (checked: 1358 of 1358 at 4.000 mm), plus a two-face rim per hem edge. So the lining is not cut
on its own: mpqem cuts the skirt and re-emits the lining from the surviving skirt faces (twinv: per skirt face, the lining GLB
vertex of each corner, in the skirt face's corner order); the rim is kept exactly.

Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact):
- the whole head part (face skin, neck seam, eyes, teeth);
- the hood edge: hood faces within HOODEDGE m of a head-part vertex (the face/hood border is one paint, repainted several times);
- the collar: dress faces within COLLAR m of a head-part vertex; sleeve hems: dress faces within CUFF m of an arm vertex;
- the short sleeves (SLEEVE m, PeasantF3's set g: cutting them let the arm stub through in Conv1);
- soles: leg faces below floor + SOLE; connected pieces of up to SMALL faces (lacing); the lining rim.
Groups: 1 hand + fingers (seam slides), 2 hood, 3 skirt (lined), 4 shoes (below SHOE m), 5 arm skin (upper arm + forearm),
7 hidden legs (above SHOE m, inside the skirt); 0 = dress (the ladder ratio).
Usage: make_sets_pf1.py <tag>"""
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
HOODEDGE = float(E('HOODEDGE', '0.008')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.012'))
SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '80'))
SLV = float(E('SLEEVE', '0.15'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf1.glb', 'PeasantF1')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; src = g['src']
PR = ['PeasantF1_B', 'PeasantF1Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
keep = part == 0
hood_edge = (part == 1) & near(pv(0), HOODEDGE)
collar = (part == 2) & near(pv(0), COLLAR); cuff = (part == 2) & near(pv(5), CUFF)
sole = (part == 4) & (V[:, :, 1].min(1) < floor + SOLE)
sleeve = (part == 2) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
# the hood's free hem (HOODHEM m of its open boundary, set c): b50 cut it at 0.65 and the hem fold shaded as a dark band in profile
HOODHEM = float(E('HOODHEM', '0'))
hood_hem = np.zeros(len(T), bool)
if HOODHEM > 0:
    from collections import Counter
    hf = np.flatnonzero(part == 1); ec = Counter(); ac = Counter()
    for f in range(len(T)):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = tuple(sorted((FTw := w[T[f]])[[a, b]].tolist())); ac[e] += 1
            if part[f] == 1:
                ec[e] += 1
    bv = np.unique([v for e, c in ec.items() if c == 1 and ac[e] == 1 for v in e])
    rep = np.zeros(w.max() + 1, int); rep[w] = np.arange(len(P))
    hood_hem = (part == 1) & near(rep[bv], HOODHEM)
    print('hood hem open-boundary positions', len(bv), 'faces', int(hood_hem.sum()))
# the hood's rolled hem (HOODFOLD m, set d): c50 kept the open boundary but the hem is mostly a closed fold (outer shell -> a
# downward underside -> inner layer); cut faces next to it interpolated the fold's down-turned vertex normals into a dark band.
# Keep hood faces within HOODFOLD of an underside face (face normal y < -0.5) or a crease face (a corner normal at < 0.7 to the face)
HOODFOLD = float(E('HOODFOLD', '0'))
hood_fold = np.zeros(len(T), bool)
if HOODFOLD > 0:
    NN = np.concatenate([D[k]['N'] for k in PR])
    fn = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    dev = np.einsum('fkc,fc->fk', NN[T], fn).min(1)
    seed = (part == 1) & ((fn[:, 1] < -0.5) | (dev < 0.7))
    hood_fold = (part == 1) & near(np.unique(T[seed]), HOODFOLD)
    print('hood fold seeds', int(seed.sum()), 'faces', int(hood_fold.sum()))
keep |= hood_edge | collar | cuff | sole | sleeve | hood_hem | hood_fold
# connected pieces (welded by position)
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small & (part != 6)
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')

# ---- skirt -> lining twins (body primitive only, local indices)
s = np.load(HERE.parent / 'mm9_peasantf1_claude' / 'work' / 'uv_tex2.npz')
stri = s['tri']; sco = s['co'][:, [0, 2, 1]] * [-1, 1, -1]          # glb_parts' frame (x mirrored, y up)
sp = s['comp'][stri[:, 0]]; S_ = np.flatnonzero(sp == 3); L_ = np.flatnonzero(sp == 6)
s2l = {int(a): int(b) for a, b in zip(S_, L_[:len(S_)])}           # npz skirt face k -> npz lining face k (reversed)
nb = len(D['PeasantF1_B']['T']); TB = D['PeasantF1_B']['T']; PB = D['PeasantF1_B']['P']
bpart = part[:nb]; bsrc = src[:nb]
key = lambda q: tuple(np.round(q, 5))
lin_by_pos = {}
for f in np.flatnonzero(bpart == 6):
    lin_by_pos.setdefault(frozenset(key(PB[v]) for v in TB[f]), []).append(int(f))
twinv = -np.ones((nb, 3), np.int64); twinf = -np.ones(nb, np.int64); bad = 0; resid = []; taken = set()
for f in np.flatnonzero(bpart == 3):
    ns = int(bsrc[f]); nl = s2l[ns]
    # npz skirt corner j at the GLB corner k (exact positions); npz lining corner of skirt corner j is 2 - j
    js = [int(np.argmin(np.linalg.norm(sco[stri[ns]] - PB[TB[f, k]], axis=1))) for k in range(3)]
    want = [sco[stri[nl][2 - j]] for j in js]
    cands = sorted(lin_by_pos.get(frozenset(key(q) for q in want), []), key=lambda lf: lf in taken)
    best = None
    for lf in cands:
        corner = [int(np.argmin(np.linalg.norm(PB[TB[lf]] - q, axis=1))) for q in want]
        e = max(np.linalg.norm(PB[TB[lf, c]] - q) for c, q in zip(corner, want))
        if len(set(corner)) == 3 and (best is None or e < best[0] - 1e-9):
            best = (e, lf, corner)
    if best is None or best[0] > 1e-5:
        bad += 1; continue
    resid.append(best[0]); twinf[f] = best[1]; twinv[f] = TB[best[1], best[2]]; taken.add(best[1])
used = np.zeros(nb, bool); used[twinf[twinf >= 0]] = True
rim = (bpart == 6) & ~used
print('twins: skirt faces', int((bpart == 3).sum()), 'matched', int((twinf >= 0).sum()), 'unmatched', bad,
      'max corner residual', max(resid) if resid else None, '| lining faces twinned', int(used.sum()), 'rim', int(rim.sum()),
      '| lining faces used twice', int(len(twinf[twinf >= 0]) - len(np.unique(twinf[twinf >= 0]))))
assert bad == 0
# offset check: lining corner 4 mm from its skirt corner
dd = np.linalg.norm(PB[twinv[twinf >= 0]] - PB[TB[twinf >= 0]], axis=2)
print('twin offset mm min', dd.min() * 1000, 'max', dd.max() * 1000)

rimF = np.zeros(len(T), bool); rimF[:nb] = rim
lining = np.zeros(len(T), bool); lining[:nb] = (bpart == 6) & used
lined = part == 3
keep |= rimF
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 5) & handj[joint]] = 1; group[(part == 5) & ~handj[joint]] = 5
group[part == 1] = 2; group[part == 3] = 3
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == 4) & low] = 4; group[(part == 4) & ~low] = 7
group[keep] = 0
names = g['names']
for p_ in np.unique(part):
    m = part == p_
    print(f'part {p_} {names[p_]:7s} {m.sum():5d} keep {int((m & keep).sum()):5d} free {int((m & ~keep & ~lining).sum()):5d} '
          f're-emitted {int((m & lining).sum()):5d} groups',
          {int(k): int((group[m & ~keep & ~lining] == k).sum()) for k in np.unique(group[m & ~keep & ~lining])})
print('hood fold', int((hood_fold & ~hood_hem & ~hood_edge).sum()), 'hood hem', int((hood_hem & ~hood_edge).sum()), 'hood edge', int(hood_edge.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'sleeves', int(sleeve.sum()),
      'soles', int(sole.sum()), 'small', int((small & (part != 6)).sum()), 'rim', int(rimF.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining (follows the skirt)', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(T))
twv = -np.ones((len(T), 3), np.int64); twv[:nb] = twinv
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, part=part, mat=g['mat'],
         twinv=twv, rim=rimF)
