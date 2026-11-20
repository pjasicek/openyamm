#!/usr/bin/env python3
"""Keep set and region groups for the m362 ladder (work/pieces.npy, soles.npy, regmask.npy, visible_head.npy,
visible_all.npy, groups.npz; labels from m362_pieces.py).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3), the eyes and mouth, the belt
studs and chest laces, the whole sheathed rapier (thin scabbard tube and small hilt pieces taper at any cut), the soles
(boot faces below 6 cm), the visible face front (head skin seen in some view, in front of y = FRONT_Y, |x| < 7.5 cm,
above the chin line CHIN_Z), and every face on a painted region edge of the doublet (mask R between 0.1 and 0.9: the
white stripes on the doublet and the shoulder rolls) or the hairline (G), so the recolour seams stay where they are.
Groups (ratios on the run_ladder.sh line): 1 visible head sides and back, 2 hidden head skin, 3 doublet, 4 hair,
5 breeches, 6 hidden body skin (never seen), 7 shirt sleeves and cuffs, 8 shoulder rolls, 9 doublet skirt, collar,
belt and boot cuffs, 10 boot uppers; label 0 (visible neck and chest skin) takes the free ratio.
Usage: m362_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy   (M362_EXTRA_KEEP=<npy,...> adds patch sets)"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); rm = np.load('work/regmask.npy')
seen_h = np.load('work/visible_head.npy'); seen = np.load('work/visible_all.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
headw = W[:, [i for i, n in enumerate(names) if n in ('B_Head', 'B_Neck')]].sum(1)
FRONT_Y, CHIN_Z = float(os.environ.get('FRONT_Y', '-0.01')), float(os.environ.get('CHIN_Z', '1.46'))
skin = p == 1
head = skin & (headw[f].mean(1) > 0.5) & (c[:, 2] > 1.40)
vis = head & (seen_h > 0)
front = vis & (c[:, 1] < FRONT_Y) & (np.abs(c[:, 0]) < 0.075) & (c[:, 2] > CHIN_Z)   # eyes, nose, mouth, chin
edge = ((rm[:, 0] > .1) & (rm[:, 0] < .9)) | (((rm[:, 1] > .1) & (rm[:, 1] < .9)) & np.isin(p, [1, 5]))
keep = ((hand[f] > 0.3).any(1) | np.isin(p, [3, 4, 11, 12, 13]) | soles | front | edge)
extra = os.environ.get('M362_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[vis & ~front] = 1; groups[head & ~vis] = 2
groups[p == 2] = 3; groups[p == 5] = 4; groups[p == 6] = 5
groups[skin & ~head & (seen == 0)] = 6
groups[p == 8] = 7; groups[p == 9] = 8; groups[p == 10] = 9; groups[(p == 7) & ~soles] = 10
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face front', int((front & keep).sum()), 'paint edge', int((edge & keep).sum()),
      'hands', int(((hand[f] > 0.3).any(1)).sum()), ')', {k: int((groups == k).sum()) for k in range(11)},
      'free', int(((groups == 0) & ~keep).sum()))
