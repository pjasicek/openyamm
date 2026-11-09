#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantM1_A, PeasantM1Head) for mpqem.py ->
work/glb_sets_<tag>.npz. PeasantM2d's make_sets_pm2d.py recipe (set h) on PeasantM1d's parts (glb_parts.py):
Keep exactly (REDUCTION_BRIEF_20261104 relaxed set for prio-2 townsfolk, face exact):
- face shell (20: face, ears, scalp, neck) and eyes/mouth pieces (22) whole; hair faces within HAIREDGE m of a hair piece's
  open rim where that rim lies on the skin (within SKIN m of the face shell: the hairline);
- collar: shirt faces within COLLAR m of a face-shell vertex (neck seam); cuffs: shirt faces within CUFF m of the shirt's open
  rim near the hands (sleeve ends over the hand graft); soles (boot faces below floor + SOLE); pieces of up to SMALL faces
  (belt + buckle, front laces, boot buckles);
- SHOULDER=1: shirt faces touching a vertex dominated by a Clavicle or UpperArm joint (the jitter gate's shoulder-skin sample;
  PeasantM2d b60 failed it when that cloth was cut).
Groups: 1 hand + fingers (seam slides), 5 forearm skin of the MPFB hand piece, 2 hair, 4 boots + boot cuffs, 6 breeches,
0 = shirt (the ladder ratio).
Usage: make_sets_pm1d.py <tag>  (env HAIREDGE, COLLAR, CUFF, SOLE, SMALL, SHOULDER, EXTRA=<npy of extra keep faces>)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
HAIREDGE = float(E('HAIREDGE', '0.012')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.04'))
SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '80'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm1.glb', 'PeasantM1')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = [str(x) for x in g['jnames']]; joint = g['joint']
PR = ['PeasantM1_A', 'PeasantM1Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = g['voff']
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
assert len(T) == len(part)
floor = P[:, 1].min(); V = P[T]
pv = lambda m: np.unique(T[m].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
rep = np.zeros(w.max() + 1, np.int64); rep[w] = np.arange(len(w))


def rim(mask):
    ec = {}
    for f in np.flatnonzero(mask):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (min(FT[f, a], FT[f, b]), max(FT[f, a], FT[f, b])); ec[e] = ec.get(e, 0) + 1
    return P[rep[np.unique([x for e, c in ec.items() if c == 1 for x in e])]]


keep = np.isin(part, (20, 22))
collar = (part == 1) & near(pv(part == 20), COLLAR)
srim = rim(part == 1); handP = P[pv(part == 0)]
rim_cuff = srim[cKDTree(handP).query(srim)[0] < 0.12]
print('shirt open rim verts', len(srim), 'near hands', len(rim_cuff))
cuff = (part == 1) & (cKDTree(rim_cuff).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < CUFF)
hrim = rim(part == 21)
# hair pieces are open cards (rim vertices are locked by mpqem anyway); the hairline is the hair within HAIREDGE of the rim
# vertices that lie on the skin (within SKIN m of a face-shell vertex): the forehead, temple and nape edge
hrim = hrim[cKDTree(P[pv(part == 20)]).query(hrim)[0] < float(E('SKIN', '0.005'))]; print('hair rim verts on the skin', len(hrim))
hairline = (part == 21) & (cKDTree(hrim).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HAIREDGE) if len(hrim) else np.zeros(len(T), bool)
sole = np.isin(part, (6, 8)) & (V[:, :, 1].min(1) < floor + SOLE)
small = part == 9
keep |= hairline | collar | cuff | sole | small
shoulder = np.zeros(len(T), bool)
if E('SHOULDER', '0') == '1':
    dom = J[np.arange(len(J)), W.argmax(1)]
    sj = np.array([('Clavicle' in x or 'UpperArm' in x) for x in jn])
    shoulder = (part == 1) & sj[dom[T]].any(1); keep |= shoulder
# RIM=<m>: the openings the see-through gate looks into (shirt hem, breeches waist and cuffs, boot and boot-cuff tops) keep the
# faces within RIM m of their part's open rim (b70 raised the corpse's hem view, Dead torso 920 -> 981 px, and Fidget 232 -> 280)
openings = np.zeros(len(T), bool)
if float(E('RIM', '0')) > 0:
    nk = cKDTree(P[pv(part == 20)])
    for p_ in (1, 5, 6, 8):
        r_ = rim(part == p_)
        if p_ == 1:
            r_ = r_[(cKDTree(handP).query(r_)[0] >= 0.12) & (nk.query(r_)[0] >= 0.03)]
        if len(r_):
            openings |= (part == p_) & (cKDTree(r_).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < float(E('RIM', '0')))
    keep |= openings
    print('openings kept', int(openings.sum()), {int(p_): int((openings & (part == p_)).sum()) for p_ in (1, 5, 6, 8)})
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); keep |= ex; print('extra keep', x, int(ex.sum()))
handj = np.array([any(t in x for t in (' Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 0) & handj[joint]] = 1; group[(part == 0) & ~handj[joint]] = 5
group[part == 21] = 2; group[np.isin(part, (6, 8))] = 4; group[part == 5] = 6
group[keep] = 0
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('hairline', int(hairline.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'soles', int(sole.sum()),
      'small', int(small.sum()), 'shoulder', int((shoulder & ~(collar | cuff)).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
z = np.zeros(len(T), bool)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=z, lined=z, pair=g['pair'],
         twin=g['twin'], part=part, mat=g['mat'])
