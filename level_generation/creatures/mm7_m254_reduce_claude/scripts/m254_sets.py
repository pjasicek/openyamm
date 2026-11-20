#!/usr/bin/env python3
"""Keep set and region groups for the m254 Golem ladder (work/pieces.npy, soles.npy, visible_head.npy, groups.npz).
Kept exactly: both hands and fingers (body-skin faces touching a vertex with hand + finger weight > 0.3), the sole
faces (below 6 cm), the visible face (head-set skin seen from some view: work/visible_head.npy), the rigid small
ornaments (eyes, ear studs, 24 collar studs, horns) and anything in M254_KEEP (comma list of piece ids, e.g. 5,6,8 to
keep crown, nemes and beard) or M254_EXTRA_KEEP (.npy masks: patches, drift locks).
Groups (decimated on their own; ratios on the run_ladder.sh command line): 1 head skin within M254_VIS_RINGS rings of a
visible face (not kept), 2 hidden head skin (scalp under the nemes and crown, neck under the beard), 3 loincloth,
4 collar, 5 crown, 6 nemes, 7 belt, 8 beard, 9 horn sockets, 10 cuffs, 11 hands (M254_HAND_GROUP=1 only), 12 fingertips (M254_TIP_GROUP=1 too); label 0 (body skin: torso, arms, legs) takes
the ladder budget. Usage: m254_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
E = os.environ.get
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); seen = np.load('work/visible_head.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 1; vis = head & (seen > 0); face = vis.copy()
for _ in range(int(E('M254_VIS_RINGS', '1'))):
    vv = np.zeros(len(v), bool); vv[f[vis]] = True; vis = head & vv[f].any(1)
hands = (p == 2) & (hand[f] > 0.3).any(1)
HANDGRP = E('M254_HAND_GROUP') == '1'  # hands and fingers as group 11 (decimated gently) instead of kept
keep = face | (hands & (not HANDGRP)) | soles | np.isin(p, [9, 12, 13, 14])
for k in [int(x) for x in E('M254_KEEP', '').split(',') if x]:
    keep |= p == k
for x in [x for x in E('M254_EXTRA_KEEP', '').split(',') if x]:
    keep |= np.load(x)
groups = np.zeros(len(f), int)
groups[vis & ~face] = 1; groups[head & ~vis] = 2
for lab, piece in ((3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 11), (10, 10)):
    groups[p == piece] = lab
if HANDGRP:
    groups[hands] = 11
    # fingertips (distal phalanges, weight > 0.3) as group 12 (their own gentler ratio)
    import re
    tipw = W[:, [i for i, n in enumerate(names) if re.search(r'Finger(\d2|0\.002)$', n)]].sum(1)
    if E('M254_TIP_GROUP') == '1':
        groups[hands & (tipw[f] > 0.3).any(1)] = 12
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face', int(face.sum()), 'hands', int(hands.sum()), 'soles', int(soles.sum()), ')',
      {k: int((groups == k).sum()) for k in range(13)}, 'free', int(((groups == 0) & ~keep).sum()))
