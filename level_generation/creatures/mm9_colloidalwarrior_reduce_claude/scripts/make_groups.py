#!/usr/bin/env python3
"""Per-face keep mask and groups for the Colloidal Warrior (mm9_colloidalwarrior, 12,520 LOD0 triangles in one skinned
node `Colloidal`: body set 7,994 incl. both grafted MPFB hands, head set 4,526: the face and the hood dome over the
hunched trunk). Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104.md).
Kept exactly (work/keep.npy):
- the head set's face and its neck seam (head set minus work/head_hood.npy from head_classes.py);
- the hand-graft junction: faces with any Forearm weight >= 0.02 that also carry a hand/finger weight, plus the faces
  with a hand weight but not wholly on the hand (the wrist), and with FINGERTIPS=1 the 2nd/3rd phalanges;
- the soles (all three corners within SOLE_Z of the rest floor);
- with KEEP_ERR, extra faces (err_lock.py output).
Groups (work/groups.npy): 0 the rest of the body (trunk, arms, legs, feet: the ladder budget), 5 the hood at
HOOD_RATIO, 6 the hands (palm, back, fingers apart from the kept parts) at HAND_RATIO."""
import os
import numpy as np
SOLE_Z = float(os.environ.get('SOLE_Z', '0.04'))
d = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz')
f, v = d['faces'], d['verts']; mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
W = sw['weights']; names = [str(n) for n in sw['names']]
dom = np.load('work/faces_info.npz')['dom'].astype(str)
head = mat == 1
hood = np.load('work/head_hood.npy')
hk = [i for i, s in enumerate(names) if any(k in s for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
hw = W[:, hk].sum(1)[f]
hand = (hw.max(1) >= 0.01) & ~head
fw = W[:, [i for i, s in enumerate(names) if 'Forearm' in s]].sum(1)[f].max(1)
graft = hand & ((fw >= 0.02) | (hw.min(1) <= 0.99))
tips = np.array([any(x.endswith(k) for k in ('2', '3', '01', '02', '11', '12', '21', '22', '31', '32', '41', '42')) and
                 any(k in x for k in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for x in dom]) & hand
if os.environ.get('FINGERTIPS', '0') != '1':
    tips[:] = False
z = v[:, 2]; soles = (z[f] < z.min() + SOLE_Z).all(1) & ~head
g = np.zeros(len(f), int)
g[hood] = 5
g[hand & ~graft & ~tips] = 6
keep = (head & ~hood) | graft | tips | soles
if os.environ.get('KEEP_ERR'):
    for p in os.environ['KEEP_ERR'].split(','):
        keep |= np.load(p)
ratios = {5: float(os.environ.get('HOOD_RATIO', '0.7')), 6: float(os.environ.get('HAND_RATIO', '0.7'))}
open('work/group_ratios.txt', 'w').write(','.join(f'{k}:{r}' for k, r in ratios.items()))
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
np.save('work/keep_hands.npy', graft | tips); np.save('work/keep_soles.npy', soles)
print('KEEP', int(keep.sum()), 'face+seam', int((head & ~hood).sum()), 'graft', int(graft.sum()), 'tips', int(tips.sum()),
      'soles', int(soles.sum()), '| groups free', {int(k): int(((g == k) & ~keep).sum()) for k in sorted(set(g.tolist()))},
      'ratios', ratios)
