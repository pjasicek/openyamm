#!/usr/bin/env python3
"""Keep set and region groups for the m322 ladder (work/pieces.npy from m322_pieces.py, soles.npy, regmask.npy,
visible_head.npy, groups.npz).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3: the left fist holds the staff
with a solved grip), the eyes and mouth bits, the vest lacing and every small piece (studs, trouser grommets: their
ends taper into points at any cut), the boot soles (faces below 6 cm), the visible face front (head-skin faces seen
in some view, in front of y = -0.04), the trousers' open side lacing (skin-shell faces on the legs outside the trousers
mask: painted laces bend under any collapse) and the trouser faces on the mask border beside it (0.05 < R < 0.95).
Groups (decimated on their own, ratios on the run_ladder.sh line): 1 visible head sides (ears, temples, hairline),
2 hidden head skin (under the hair), 3 hair, 4 trousers, 5 boots, 6 vest; label 0 (bare arms, shoulders, belly, back,
neck) takes the free ratio. Usage: m322_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy
(M322_EXTRA_KEEP=<npy,...> adds patch sets)"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); seen = np.load('work/visible_head.npy')
rm = np.load('work/regmask.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
legw = W[:, [i for i, n in enumerate(names) if any(k in n for k in ('Thigh', 'Calf'))]].sum(1)
head = p == 2; vis = head & (seen > 0); front = vis & (c[:, 1] < -0.04)
lacing = (p == 1) & (legw[f].mean(1) > 0.5) & (c[:, 2] < 1.0)
border = (p == 4) & (rm[:, 0] > 0.05) & (rm[:, 0] < 0.95)
keep = (hand[f] > 0.3).any(1) | np.isin(p, [7, 8, 9]) | soles | front | lacing | border
# RING (default 0): grow the lacing/border keep by face rings (set d: a trouser collapse beside the strip dragged a
# pale lacing texel onto the right shin)
lb = lacing | border
for _ in range(int(os.environ.get('RING', '0'))):
    vk = np.zeros(len(v), bool); vk[f[lb].ravel()] = True; lb = vk[f].any(1)
keep |= lb
extra = os.environ.get('M322_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
grp = np.zeros(len(f), int)
grp[vis & ~front] = 1; grp[head & ~vis] = 2; grp[p == 3] = 3; grp[p == 4] = 4; grp[p == 5] = 5; grp[p == 6] = 6
grp[keep] = 0
name = sys.argv[1]
np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', grp)
print('SET', name, 'kept', int(keep.sum()), {k: int((grp == k).sum()) for k in range(7)}, 'lacing', int(lacing.sum()), 'border', int(border.sum()), 'front', int(front.sum()))
