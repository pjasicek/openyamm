#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face of the Green Man (prims GreenMan (body shell + body leaf cards), GreenManHead (head
shell with the face, beard/hood leaf cards, crown branches, MPFB hands, staff)) for mpqem.py -> work/glb_sets_<tag>.npz
(keep, group, lining, lined: no linings on this model).
Classes from classify.py (work/classes.npz): 0 body shell, 1 head shell, 2 hands, 3 staff, 4 bark, 5 leaf.
Keep exactly: the head shell (face skin, eyes, lips, ears, neck seam: one component); every leaf card (closed 2-100 face shells:
no interior vertex to remove without moving a leaf edge) unless LEAFCUT (faces of leaf components with more than LEAFMIN faces
go to group 5); body faces within NECK m of the head shell, within WRIST m of the hands (forearm rim tapered onto the hand
stub), soles (within SOLE m of the floor); hand faces dominated by a Forearm joint (graft junction) and the fingertips (within
TIP m of a finger's distal end, per finger component of the distal joint); staff faces within GRIP m of the posed R hand in
any sampled frame of Standing, Walking and Fidget (the grip contact); faces of components up to SMALL faces.
Cut groups: 0 body shell (ladder ratio), 1 hands, 2 staff, 3 crown branches + wrist bark, 5 large leaf comps (LEAFCUT=1).
Usage: make_sets_gm.py <tag>  (env NECK, WRIST, SOLE, TIP, GRIP, SMALL, LEAFCUT, LEAFMIN, KEEPBODY=<npy of extra kept faces>)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glbio  # noqa: E402
from glb_pose import Glb, Model  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
NECK = float(E('NECK', '0.015')); WRIST = float(E('WRIST', '0.015')); SOLE = float(E('SOLE', '0.012'))
TIP = float(E('TIP', '0.008')); GRIP = float(E('GRIP', '0.03')); SMALL = int(E('SMALL', '40'))
LEAFCUT = E('LEAFCUT', '0') == '1'; LEAFMIN = int(E('LEAFMIN', '40'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'GreenMan')
PR = ['GreenMan', 'GreenManHead']
s = np.load(HERE / 'work' / 'survey.npz'); c = np.load(HERE / 'work' / 'classes.npz')
jn = [str(x) for x in s['jnames']]; joint = s['joint']; comp = s['comp']; csize = s['csize']; cls = c['cls']
voff = np.cumsum([0] + [len(D[k]['P']) for k in PR])
P = np.concatenate([D[k]['P'] for k in PR]); T = np.concatenate([D[k]['T'] + voff[i] for i, k in enumerate(PR)])
n = len(T); V = P[T]; cen = V.mean(1)
keep = np.zeros(n, bool); why = np.zeros(n, np.int64)


def mark(m, code):
    new = m & ~keep; keep[new] = True; why[new] = code


def near(m_src, m_dst, d):
    tree = cKDTree(P[np.unique(T[m_dst])])
    return m_src & (tree.query(V.reshape(-1, 3))[0].reshape(n, 3).min(1) < d)


mark(cls == 1, 1)                                                     # head shell (face exact)
if LEAFCUT:
    mark((cls == 5) & (csize <= LEAFMIN), 2)
else:
    mark(cls == 5, 2)                                                 # leaf cards
mark(near(cls == 0, cls == 1, NECK), 3)                               # neck seam
mark(near(cls == 0, cls == 2, WRIST), 4)                              # wrist rim on the hand stub
floor = P[:, 1].min()
mark((cls == 0) & (V[:, :, 1].min(1) < floor + SOLE), 5)              # soles
mark((cls == 2) & np.array(['Forearm' in jn[j] for j in joint]), 6)   # hand-graft junction
# fingertips: faces with a vertex within TIP of the farthest vertex (from the hand joint) of each distal-joint component
tips = np.zeros(n, bool)
for j, name in enumerate(jn):
    if not (name.endswith('3') or name.endswith('2') and 'Finger0' in name) or ('L ' not in name and 'R ' not in name):
        continue
    m = (cls == 2) & (joint == j)
    if not m.any():
        continue
    hand = jn.index(name.split(' ')[0] + ' ' + name.split(' ')[1] + ' Hand')
    hc = P[np.unique(T[(cls == 2) & (joint == hand)])].mean(0)
    vs = np.unique(T[m]); far = P[vs][np.argmax(np.linalg.norm(P[vs] - hc, axis=1))]
    tips |= m & (np.linalg.norm(V - far, axis=2).min(1) < TIP)
mark(tips, 7)
# staff grip: staff faces within GRIP of the posed R hand in sampled frames
model = Model(Glb(str(HERE / 'before' / 'mm9_greenman.glb')))
rh = np.unique(T[(cls == 2) & (cen[:, 0] < 0)]); st = np.unique(T[cls == 3])
grip_v = np.zeros(len(P), bool)
for clip in ('Standing', 'Walking', 'Fidget', 'Fidget2', 'Running', 'AttackMelee'):
    t1 = model.clip_times(clip)[-1]
    for t in np.linspace(0, t1, 9):
        posed = np.concatenate([p for p, _ in model.skinned_positions(model.world(model.sample(clip, t)))])
        d, _ = cKDTree(posed[rh]).query(posed[st]); grip_v[st[d < GRIP]] = True
mark((cls == 3) & grip_v[T].any(1), 8)
mark(csize <= SMALL, 9)
if E('KEEPBODY', ''):
    mark(np.load(E('KEEPBODY', '')), 10)
group = np.zeros(n, np.int64)
group[cls == 2] = 1; group[cls == 3] = 2; group[cls == 4] = 3; group[cls == 5] = 5
group[keep] = 0
z = np.zeros(n, bool)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=z, lined=z, why=why, cls=cls)
names = {1: 'head shell', 2: 'leaf cards', 3: 'neck seam', 4: 'wrist rim', 5: 'soles', 6: 'hand junction', 7: 'fingertips',
         8: 'staff grip', 9: 'small comps', 10: 'extra'}
print('SETS', tag, 'faces', n, 'kept', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', {names[k]: int((why == k).sum()) for k in names})
print('  free per group', {int(g): int(((group == g) & ~keep).sum()) for g in np.unique(group[~keep])})
print('  15 % of LOD0 =', int(0.15 * n), 'faces; free', int((~keep).sum()), '-> needs', f'{0.15 * n / max((~keep).sum(), 1) * 100:.0f} % of the free faces')
