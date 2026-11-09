#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (file primitive order: PeasantBoy_A body, PeasantBoyHead) for mpqem.py ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, pair). Peasant boy copy (2026-11-05) of the Dwarf boy's
make_sets_dboy.py; parts by welded connected component (scripts/analyze.py), classified explicitly for this body:
body prim: 0 cloth (vest, sleeves + forearms, the vest skirt under the belt), 1 legs (trousers, lower legs, boots), 2 small pieces
(belt, toggle placket, toggles: < SMALL faces), 6 the waist backstop tube (waist_backstop.py: one closed one-texel piece inside the
trunk); head prim: 3 head (head shell: face skin, ears, eyes, scalp; the neck piece), 4 hair (bob shell), 5 hands (MPFB grafts).
Linings from work/twins.npz (twins.py): paired linings are dropped from the cut and re-emitted by mpqem.py from the surviving lined
faces.
Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact):
- the head part (except the scalp under the hair with SCALP > 0); small pieces;
- the collar: cloth faces within COLLAR m of a head-part vertex (neck seam);
- the graft junction: body faces within GRAFT m of a hand vertex and hand faces within GRAFT m of a body vertex;
- soles: leg faces below floor + SOLE;
- rim strips (faces on a lining vertex), unpaired one-texel faces other than the tube (linings without a twin) and the outer
  faces within HALO m of their vertices; lining pairs where both sides carry UVs.
- SHOULDER=1: cloth faces on a clavicle / upper-arm dominated vertex (the Dwarf boy's jitter lesson).
Groups: 1 hands (seam slides), 2 hair, 3 legs, 5 scalp under the hair, 6 tube (one-texel collapse allowed), 0 = cloth (ladder).
Usage: make_sets_boy.py <tag>   (env SMALL, COLLAR, GRAFT, SOLE, HALO, SHOULDER, SCALP)"""
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
SMALL = int(E('SMALL', '300')); COLLAR = float(E('COLLAR', '0.01')); GRAFT = float(E('GRAFT', '0.015'))
SOLE = float(E('SOLE', '0.012')); HALO = float(E('HALO', '0.006')); SC = float(E('SCALP', '0'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantboy.glb', 'PeasantBoy')
PR = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
assert PR == ['PeasantBoy_A', 'PeasantBoyHead'], PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
tw = np.load(HERE / 'work' / 'twins.npz')
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
nb0 = len(D[PR[0]]['T'])
mat = np.concatenate([[i] * len(D[k]['T']) for i, k in enumerate(PR)])
zero = np.concatenate([tw[f'zero_{k}'] for k in PR])
lining = tw['lining'].astype(bool); lined = tw['lined'].astype(bool)
pair = np.concatenate([np.where(tw[f'pair_{k}'] >= 0, tw[f'pair_{k}'] + (0 if i == 0 else nb0), -1) for i, k in enumerate(PR)])
assert len(lining) == len(T)
floor = P[:, 1].min()
V = P[T]
_, w = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True)
w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl, minlength=lab.max() + 1)
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
acc = np.zeros((len(T), len(jn)))
for c in range(3):
    for i in range(4):
        np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
dj = acc.argmax(1); djn = np.array(jn)[dj]
LEG = ('Thigh', 'Calf', 'Foot', 'Toe')
HAND = ('Hand', 'Forearm', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
part = -np.ones(len(T), int)
for cmp in np.unique(fl):
    m = fl == cmp; k = int(mat[m][0]); names = djn[m]
    if k == 0:
        if zero[m].all() and m.sum() > 1000:
            part[m] = 6
        elif m.sum() < SMALL:
            part[m] = 2
        elif np.mean([any(x in s for x in LEG) for s in names]) > 0.5:
            part[m] = 1
        else:
            part[m] = 0
    else:
        if np.mean([any(x in s for x in HAND) for s in names]) > 0.5:
            part[m] = 5
        elif m.sum() > 1500 or np.mean(['Neck' in s for s in names]) > 0.5:
            part[m] = 3
        else:
            part[m] = 4
assert (part >= 0).all()
pv = lambda *ps: np.unique(T[np.isin(part, ps)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = (part == 3) | ((part == 2) & ~lining)
collar = (part == 0) & near(pv(3), COLLAR)
graft = (part == 0) & near(pv(5), GRAFT) | ((part == 5) & near(pv(0), GRAFT))
sole = (part == 1) & (V[:, :, 1].min(1) < floor + SOLE)
_, tp = np.unique(np.c_[np.round(P, 6), np.repeat(np.arange(len(PR)), np.diff(offs))], axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lining].ravel()]] = True
strip = ~lining & (part != 6) & linp[tp[T]].any(1)
loose = zero & ~lining & ~strip & (part != 6)
halo = ~lining & ~(part == 3) & (part != 6) & (near(np.unique(T[loose | strip].ravel()), HALO) if (loose | strip).any() else False)
uvpair = (lining & ~zero)
uvpair_both = uvpair.copy(); uvpair_both[pair[uvpair]] = True
keep |= collar | graft | sole | strip | loose | halo | uvpair_both
if E('SHOULDER', '0') == '1':
    dv = np.array([jn[J[i][W[i].argmax()]] for i in range(len(J))])
    shv = np.array([('Clavicle' in x or 'UpperArm' in x) for x in dv])
    shoulder = (part == 0) & ~lining & shv[T].any(1)
    print('shoulder faces kept', int((shoulder & ~keep).sum())); keep |= shoulder
# scalp under the hair (the girls' scalp_dist.py inline): head-shell faces whose normal ray meets the hair within 4 cm and that lie
# more than SCALP m from the hair shell's open edges: group 5 (vertex removal takes surface chords: the scalp moves inward)
scalp = np.zeros(len(T), bool)
if SC > 0:
    hd = np.flatnonzero((part == 3) & (mat == 1)); hr = np.flatnonzero(part == 4)
    shell = hd[fl[hd] == np.bincount(fl[hd]).argmax()]
    c = V[shell].mean(1); nn = np.cross(V[shell, 1] - V[shell, 0], V[shell, 2] - V[shell, 0]); nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    A = V[hr, 0]; E1 = V[hr, 1] - A; E2 = V[hr, 2] - A
    dist = np.full(len(shell), np.inf)
    for i0 in range(0, len(shell), 256):
        o = c[i0:i0 + 256, None, :]; d = nn[i0:i0 + 256, None, :]
        pvv = np.cross(d, E2[None]); det = (E1[None] * pvv).sum(-1); inv = 1 / np.where(np.abs(det) < 1e-12, np.nan, det)
        tv = o - A[None]; u = (tv * pvv).sum(-1) * inv; qv = np.cross(tv, E1[None]); v = (d * qv).sum(-1) * inv
        t = (E2[None] * qv).sum(-1) * inv
        ok = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
        dist[i0:i0 + 256] = np.nanmin(np.where(ok, t, np.inf), 1)
    ed = {}
    for t_ in FT[hr]:
        for a, b_ in ((t_[0], t_[1]), (t_[1], t_[2]), (t_[2], t_[0])):
            k = (min(a, b_), max(a, b_)); ed[k] = ed.get(k, 0) + 1
    bv = np.unique([x for k, v in ed.items() if v == 1 for x in k]); Pw = np.zeros((n, 3)); Pw[w] = P
    de = cKDTree(Pw[bv]).query(c)[0]
    sel = shell[(dist < 0.04) & (de > SC)]
    scalp[sel] = True; keep[sel] = False
    print('head shell', len(shell), 'under the hair', int((dist < 0.04).sum()), 'scalp group (edge distance >', SC, ')', len(sel))
group = np.zeros(len(T), int)
group[part == 5] = 1; group[part == 4] = 2; group[part == 1] = 3; group[scalp] = 5; group[part == 6] = 6
group[keep] = 0
NAMES = ['cloth', 'legs', 'small', 'head', 'hair', 'hands', 'tube']
for p_ in range(7):
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
