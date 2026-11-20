#!/usr/bin/env python3
"""Keep set and region groups for the m282 Medusa ladder (work/pieces.npy, headset.npy, groups.npz; piece ids of the
batch I master: 0 skin, 5/6 hands, 17 hair snakes, 17/18 scale-mail cups, 19 collar, 20 quiver, 21/22 arm rings,
28/30 eyes, small studs and quiver arrows, 99 bow string).
Kept exactly (the user accepted the face twice: its geometry, normals and texture must not change):
- the whole head texture set (face, scalp, ears, neck top; u > 0.51 in the merged atlas) and the eyes;
- M282_HEAD_RINGS (default 2) vertex rings of body skin around it (the neck seam blend under the jaw);
- both hands with every finger (pieces 5/6 and every face touching a vertex with hand + finger weight > 0.3);
- the collar and both arm rings (thin bands go wavy at any cut), the string tube and every piece of up to
  M282_SMALL (default 80) faces (studs, quiver arrows, the three small hair curls);
- M282_EXTRA_KEEP: comma list of extra keep masks (patch_keep.py / drift_lock.py results).
Groups (decimated on their own): 1 hair snakes (the 14 large ones), 2 scale-mail cups, 3 quiver,
4 serpent skin (Tail/Col/Root weight > 0.5), 0 the rest (torso and arm skin) takes the ladder budget.
Usage: m282_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
E = os.environ.get
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
p = np.load('work/pieces.npy'); head = np.load('work/headset.npy'); comp = np.load('work/component.npy')
g = np.load('work/groups.npz'); W = g['W']; names = [str(n) for n in g['names']]
FING = ('Hand_', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
hand = W[:, [i for i, n in enumerate(names) if n.startswith(FING)]].sum(1)
serp = W[:, [i for i, n in enumerate(names) if n.startswith(('Tail_', 'Col_', 'Root'))]].sum(1)
HAIR = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35]
sizes = np.bincount(comp)
small = sizes[comp] <= int(E('M282_SMALL', '80'))
headkeep = head | np.isin(p, [28, 30])
ring = headkeep.copy()
for _ in range(int(E('M282_HEAD_RINGS', '2'))):
    vv = np.zeros(len(v), bool); vv[f[ring]] = True; ring = ring | ((p == 0) & vv[f].any(1))
hands = np.isin(p, [5, 6]) | (hand[f] > 0.3).any(1)
bands = np.isin(p, [19, 21, 22, 99])
keep = ring | hands | bands | small
for x in filter(None, (E('M282_EXTRA_KEEP') or '').split(',')):
    keep |= np.load(x)
groups = np.zeros(len(f), int)
groups[np.isin(p, HAIR)] = 1
groups[np.isin(p, [17, 18])] = 2
groups[p == 20] = 3
groups[(p == 0) & (serp[f].mean(1) > 0.5)] = 4
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(head set + rings', int(ring.sum()), 'hands', int(hands.sum()), 'bands', int(bands.sum()),
      'small', int(small.sum()), ')', {k: int(((groups == k) & ~keep).sum()) for k in range(5)})
