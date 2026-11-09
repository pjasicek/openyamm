#!/usr/bin/env python3
"""Keep set and region groups for the m332 elf ladder (work/pieces.npy, soles.npy, regmask.npy, visible_head.npy,
visible_all.npy, groups.npz).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3; includes the capped stump of
the removed sixth finger), the vest studs and lacing crosses, belt, buckle, dagger and sheath pieces, the arm band, the
eyes (small pieces taper at any cut), the soles (skin-shell faces below 6 cm), the visible face front (head skin seen in
some view, in front of y = -0.06, |x| < 7.5 cm, above the chin line z 1.48), and every skin face on a painted region edge (mask R or G between 0.1 and 0.9: the
tights' waist and ankle edges, the hairline) so the recolour seams stay where they are.
Groups (ratios on the run_ladder.sh line): 1 visible head sides and back (ears, painted hair), 2 hidden head skin,
3 vest, 4 ponytail, 5 tights (skin with mask R > 0.5), 6 hidden body skin (never seen: under the vest, belt, band);
label 0 (bare arms, chest V, neck, bracers, shoe uppers) takes the free ratio.
Usage: m332_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy   (M332_EXTRA_KEEP=<npy,...> adds patch sets)"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); rm = np.load('work/regmask.npy')
seen_h = np.load('work/visible_head.npy'); seen = np.load('work/visible_all.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
headw = W[:, [i for i, n in enumerate(names) if n in ('B_Head', 'B_Neck')]].sum(1)
skin = p == 1
head = skin & (headw[f].mean(1) > 0.5) & (c[:, 2] > 1.40)
vis = head & (seen_h > 0); front = vis & (c[:, 1] < -0.06) & (np.abs(c[:, 0]) < 0.075) & (c[:, 2] > 1.48)   # eyes, nose, mouth, chin
edge = skin & (((rm[:, 0] > .1) & (rm[:, 0] < .9)) | ((rm[:, 1] > .1) & (rm[:, 1] < .9)))
keep = ((hand[f] > 0.3).any(1) | np.isin(p, [3, 4, 6, 7, 8, 9, 10, 11, 12]) | soles | front | edge)
extra = os.environ.get('M332_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[vis & ~front] = 1; groups[head & ~vis] = 2
groups[p == 2] = 3; groups[p == 5] = 4
groups[skin & ~head & (rm[:, 0] > .5)] = 5
groups[skin & ~head & (seen == 0) & (groups == 0)] = 6
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face front', int((front & keep).sum()), 'paint edge', int((edge & keep).sum()), ')',
      {k: int((groups == k).sum()) for k in range(7)}, 'free', int(((groups == 0) & ~keep).sum()))
