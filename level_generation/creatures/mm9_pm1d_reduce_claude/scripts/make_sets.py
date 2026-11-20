#!/usr/bin/env python3
"""Keep / group / drop sets per face of work/mesh_in.npz (welded source, Blender frame) for decimate_tex.py, from the finished
master's part labels on the installed GLB (work/glb_parts.npz, glb_parts.py). Thrall parts (clean_nb NAMES): 0 hands (MPFB),
1 doublet with sleeves and placket, 5 legs (shin bands in the torso set), 6 shoes, 7 skirt (MM9's six hinges), 8 fur mantle,
9 belt, 20 head shell (face skin and hair are one Meshy skin: split by head_split.py into hair, label 21 here), 22 eyes.
No linings and no weapon on the Thrall (finish_nb only plugs the mouth); the lining code below is inert.
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104):
- exact: face skin (20, with the neck and its seam under the collar), eyes (22), the belt (9, BELT=1), soles (boot faces below floor + SOLE m),
  the hand-graft junction (hand faces within JRINGS face rings of a non-hand face), grip contact (work/grip_contact.npy,
  grip_contact.py, mapped from the GLB), body contact under resting hands (work/hand_contact.npy, optional), connected
  pieces of up to SMALL faces;
- dropped and rebuilt from the reduced outer shell (reline in reduce_ladder.py): every lining face (finish_hw's inner copies);
- groups (own ratio in decimate_tex): 1 hands, 2 hair, 3 skirt (part 7), 4 shoes above the soles;
- label 0: doublet, legs, mantle (and the belt with BELT=0): the shared cut.
Also writes work/lined_<tag>.npy: per mesh_in face, the outer face had a lining twin (nearest outer face of the same part to
each lining face's centroid), for the reline. Usage: make_sets.py <tag>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.03')); JRINGS = int(E('JRINGS', '2'))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
gc[:, 2] += V[:, 2].min()                                      # GLB mesh stands on y = 0; the Blender mesh is in the rig frame
fc = V[F].mean(1)
dist, nn = cKDTree(gc).query(fc); print('face match max', dist.max()); assert dist.max() < 1e-4
part = g['part'][nn].copy(); lining = g['lining'][nn].astype(bool)
P = lambda *n: np.isin(part, n)
key = np.round(V, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[F]; nW = wv.max() + 1
keep = np.zeros(len(F), bool)
keep |= P(20, 2, 22, 30)
if E('BELT', '1') == '1':
    keep |= P(9)                                               # thin painted belt trims (Highwayman lesson)
floor = V[:, 2].min(); sole = P(6) & (V[F][:, :, 2].min(1) < floor + SOLE); keep |= sole
# hand-graft junction
hand = P(0)
# the MPFB hands are their own pieces; the graft junction is the wrist opening inside the cuff: hand faces on an open edge
ed = np.sort(np.vstack([FT[hand][:, [0, 1]], FT[hand][:, [1, 2]], FT[hand][:, [2, 0]]]), 1)
u, c = np.unique(ed, axis=0, return_counts=True)
other = np.zeros(nW, bool); other[u[c == 1].ravel()] = True; other[FT[~hand].ravel()] = True
junc = hand & other[FT].any(1)
for _ in range(JRINGS):
    hot = np.zeros(nW, bool); hot[FT[junc].ravel()] = True; junc |= hand & hot[FT].any(1)
keep |= junc
for name in ('grip_contact', 'hand_contact'):
    f = HERE / 'work' / f'{name}.npy'
    if f.exists() and E(name.upper(), '1') == '1':
        m = np.load(f); src = gc[m]
        hit = cKDTree(src).query(fc)[0] < 1e-5 if len(src) else np.zeros(len(F), bool)
        keep |= hit; print(name, int(hit.sum()))
# the hairline: the hair shell runs under the face skin there; hair faces with a vertex within HAIRLINE m of a face-skin
# vertex stay exact so the cut cannot lift the shell through the forehead or temples
HL = float(E('HAIRLINE', '0.012'))
skinv = np.unique(F[P(20, 2)].ravel())
hl = P(21) & (cKDTree(V[skinv]).query(V[F].reshape(-1, 3))[0].reshape(-1, 3).min(1) < HL)
keep |= hl; print('hairline', int(hl.sum()))
# connected pieces (by welded position)
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = (cnt[fl] <= SMALL) & ~lining; keep |= small
for p in np.unique(part):
    s = part == p; sizes = sorted(np.bincount(fl[s])[np.bincount(fl[s]) > 0].tolist(), reverse=True)
    print(f'  part {p:2d} pieces {sizes[:14]}')
# linings: dropped; their outer twins marked
drop = lining.copy()
outer = ~lining
lined = np.zeros(len(F), bool)
for p in np.unique(part[lining]):
    o = np.where(outer & (part == p))[0]; l = np.where(lining & (part == p))[0]
    dd, k = cKDTree(fc[o]).query(fc[l]); lined[o[k]] = True
    print(f'  lining part {p}: {len(l)} faces -> outer twins {len(np.unique(k))}, centroid gap median {np.median(dd)*1000:.2f} mm max {dd.max()*1000:.2f}')
keep &= ~drop
groups = np.zeros(len(F), int)
groups[P(0) & ~keep] = 1; groups[P(21) & ~keep] = 2; groups[P(7) & ~keep & ~drop] = 3; groups[P(6) & ~keep] = 4
for p in np.unique(part):
    s = part == p
    print(f'part {p:2d} {s.sum():6d} keep {int((s & keep).sum()):5d} drop {int((s & drop).sum()):5d} free {int((s & ~keep & ~drop).sum()):5d} lined {int((s & lined).sum()):4d}')
print('soles', int(sole.sum()), 'junction', int(junc.sum()), 'small', int(small.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'drop', int(drop.sum()), 'free', int((~keep & ~drop).sum()), 'of', len(F),
      '| groups', {k: int((groups == k).sum()) for k in (1, 2, 3, 4)})
for n, a in (('keep', keep), ('groups', groups), ('drop', drop), ('lined', lined)):
    np.save(HERE / 'work' / f'{n}_{tag}.npy', a)
np.save(HERE / 'work' / 'face_part.npy', part)
