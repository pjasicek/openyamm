#!/usr/bin/env python3
"""Keep set and region groups for the m442 Goblin Female ladder (work/pieces.npy, soles.npy, handw.npy, headset.npy,
regmask.npy, armw.npy, visible_head.npy; after g452_sets.py of ../mm7_7m452_reduce_claude).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3: the sickle grip is solved per
finger), the eyes (pieces 4/5), the 37 eyelets and toggles (pieces 9-44: small pieces taper to points at any cut), the
boot soles (body faces below 6 cm) and the visible face front (head-set skin seen in some view, in front of y = FRONT_Y,
not hair).
Groups (ratios on the run_ladder.sh line): 1 visible head skin sides and back (ears, neck), 2 hidden head-set faces,
3 hair (head-set faces with region mask G > 0.5: scalp, top knot, ponytail), 4 fringe and ribbon (pieces 3, 6-8, 45),
5 purple cloth on the body (region mask R > 0.5: vest trim, trousers), 6 wide sleeves (body faces with arm share > 0.5),
7 boots (body faces below 0.45 m outside the cloth); label 0 (blouse, sash, the rest) takes the free ratio.
Usage: m442_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy   (M442_EXTRA_KEEP=<npy,...> adds patch sets)"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); handw = np.load('work/handw.npy')
hs = np.load('work/headset.npy'); rm = np.load('work/regmask.npy'); aw = np.load('work/armw.npy')
seen = np.load('work/visible_head.npy')
FRONT_Y = float(os.environ.get('M442_FRONT_Y', '-0.03'))
hair = hs & (rm[:, 1] > .5); headskin = hs & (p == 0) & ~hair
vis = seen > 0
front = headskin & vis & (c[:, 1] < FRONT_Y)
small = (p >= 9) & (p != 45)
keep = handw | np.isin(p, [4, 5]) | small | soles | front
for e in filter(None, os.environ.get('M442_EXTRA_KEEP', '').split(',')):
    keep |= np.load(e)
body = (p == 0) & ~hs
groups = np.zeros(len(f), int)
groups[headskin & vis & ~front] = 1; groups[hs & ~vis & ~np.isin(p, [4, 5])] = 2; groups[hair & vis] = 3
groups[np.isin(p, [3, 6, 7, 8, 45])] = 4
groups[body & (rm[:, 0] > .5)] = 5; groups[body & (aw > .5) & (rm[:, 0] <= .5)] = 6
groups[body & (c[:, 2] < 0.45) & (rm[:, 0] <= .5)] = 7
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face front', int((front & keep).sum()), 'hands', int(handw.sum()), 'small', int(small.sum()),
      'soles', int(soles.sum()), ')', {k: int((groups == k).sum()) for k in range(8)}, 'free', int(((groups == 0) & ~keep).sum()))
