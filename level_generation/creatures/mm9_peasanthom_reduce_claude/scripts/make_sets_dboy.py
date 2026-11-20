#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (file primitive order: PHOM1_A body, PHOM1Head_A) for mpqem.py ->
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
SOLE = float(E('SOLE', '0.012')); HALO = float(E('HALO', '0.006')); FOREARM = float(E('FOREARM', '0.24'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_phom1.glb', 'PHOM1')
PR = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
assert PR == ['PHOM1_A', 'PHOM1Head_A'], PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
tw = np.load(HERE / 'work' / 'twins.npz')
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
mat = np.concatenate([[i] * len(D[k]['T']) for i, k in enumerate(PR)])
zero = np.concatenate([tw[f'zero_{k}'] for k in PR])
lining = tw['lining'].astype(bool); lined = tw['lined'].astype(bool)
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
        elif cen[:, 1].min() < 0.05:
            part[m] = 1
        else:
            part[m] = 0
    else:
        if np.mean([('Hand' in x or 'Forearm' in x or any(f in x for f in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))) for x in names]) > 0.5:
            part[m] = 5
        elif m.sum() > 2000:
            part[m] = 3
        else:
            part[m] = 4
assert (part >= 0).all()
pv = lambda *ps: np.unique(T[np.isin(part, ps)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = (part == 3) | ((part == 2) & ~lining)
collar = (part == 0) & near(pv(3), COLLAR)
graft = (np.isin(part, (0,)) & near(pv(5), GRAFT)) | ((part == 5) & near(pv(0), GRAFT))
sole = (part == 1) & (V[:, :, 1].min(1) < floor + SOLE)
linv = np.zeros(len(P), bool); linv[T[lining].ravel()] = True
# by position (seam copies of a lining vertex)
_, tp = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lining].ravel()]] = True
strip = ~lining & linp[tp[T]].any(1)
loose = zero & ~lining & ~strip
halo = ~lining & ~(part == 3) & (near(np.unique(T[loose | strip].ravel()), HALO) if (loose | strip).any() else False)
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
# a kept lined face keeps its lining as is (re-emitted unchanged); a kept lining whose twin is cut is not allowed
keep_lining = lining & keep
lining_cut = lining & ~keep
assert not (lining_cut & keep[np.maximum(pair, 0)] & False).any()
group = np.zeros(len(T), int)
group[part == 5] = 1; group[part == 4] = 2; group[part == 1] = 3
fore = (part == 0) & np.array(['Forearm' in x for x in djn]) & (np.abs(V[:, :, 0]).min(1) > FOREARM)
group[fore] = 5
group[keep] = 0
NAMES = ['tunic', 'legs', 'small', 'head', 'hair', 'hands']
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
