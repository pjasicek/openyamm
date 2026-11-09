#!/usr/bin/env python3
"""Keep set and region groups for the m410 Thief ladder (work/pieces.npy, soles.npy, regmask.npy, visible_head.npy,
groups.npz).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3: the fist draws the dagger and
the attack is authored), the wrist band and gold bangles (thin rings), the dagger sheath with its mouth piece (the
Dagger bone follows the sheath's deformed vertices), the belt with the thin chest strap, the buckle, the red face mask,
the eyes, the boot ornament, the boot soles (faces below 6 cm), the visible face front (head-piece faces seen in some
view, in front of y = -0.03), and the chest triangle that the source holds twice (one copy reversed; M410 weld).
Groups (decimated on their own, ratios on the run_ladder.sh line): 1 visible head sides, 2 hidden head skin (under the
cap and the mask), 3 knitted cap, 4 shoulder caps, 5 coin pouch, 6 pouch back piece, 7 vest (torso-shell faces with
region mask R > 0.5: the studded quilted pattern), 8 trousers, 9 boots; label 0 (bare arms, neck, collar) takes the rest.
Usage: m410_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy   (M410_EXTRA_KEEP=<npy> adds a patch set)"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); seen = np.load('work/visible_head.npy')
rm = np.load('work/regmask.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 2; vis = head & (seen > 0); front = vis & (c[:, 1] < -0.03)
# the doubled chest triangle (source LOD0 faces 6143/6145, glTF (-0.069,1.286,0.085) (-0.0095,1.308,0.089) (-0.021,1.319,0.083))
dbl = np.zeros(len(f), bool)
for q in ((-0.0691, -0.0848, 1.2861), (-0.0095, -0.0891, 1.3077), (-0.0212, -0.0835, 1.3192)):
    dbl |= (np.linalg.norm(v - np.array(q), axis=1) < 2e-4)[f].any(1)
keep = ((hand[f] > 0.3).any(1) | np.isin(p, [9, 10, 11, 12, 13, 14, 15]) | soles | front | dbl)
extra = os.environ.get('M410_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[vis & ~front] = 1; groups[head & ~vis] = 2
for lab, piece in ((3, 3), (4, 6), (5, 7), (6, 8), (8, 4), (9, 5)):
    groups[p == piece] = lab
# vest: torso-shell faces with mask R > 0.5, filled over the painted studs (mask holes) by an edge-neighbour majority
vest = (p == 1) & (rm[:, 0] > .5)
from collections import defaultdict
ef = defaultdict(list)
for i, t in enumerate(f):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        ef[(min(a, b), max(a, b))].append(i)
nb = [[] for _ in f]
for fs in ef.values():
    for i in fs:
        nb[i] += [j for j in fs if j != i]
for _ in range(2):
    vest = vest | ((p == 1) & np.array([sum(vest[j] for j in nb[i]) >= 2 for i in range(len(f))]))
groups[vest] = 7
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(doubled', int(dbl.sum()), 'face front', int((front & keep).sum()), ')',
      {k: int((groups == k).sum()) for k in range(10)}, 'free', int(((groups == 0) & ~keep).sum()))
