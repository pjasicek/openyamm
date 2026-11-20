#!/usr/bin/env python3
"""Keep set and region groups for the m214 Elf Archer ladder (work/pieces.npy, soles.npy, keep_small.npy,
visible_head.npy, visible_all.npy, groups.npz).
Kept exactly: both hands (fingers; the left fist holds the bow, the right draws the string) and every face touching a
vertex with hand + finger weight > 0.3, the forearms (tooled bracers), the bowstring, every piece of up to 80 faces
(eyes, quiver arrows and fletchings, calf lacing, belt bits, hair tie), the soles (faces below 6 cm), the visible
face front (head-piece faces seen from some view, in front of M214_FACE_Y, above the chin) and both pointed ears
(head-piece faces farther than M214_EAR_X from the head axis between 1.56 and 1.72 m).
Groups (decimated on their own): 2 visible rest of the head skin (sides, back of the neck, under the chin),
3 hidden head-piece skin (scalp under the hair, skin under the vest: no view sees it), 4 hair, 5 quiver,
6 waist straps, 7 pouches (the two large ones), 8 visible chest and midriff skin; label 0 (vest, trousers, feet)
takes the rest of the ladder budget.
Usage: m214_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); small = np.load('work/keep_small.npy')
seen_h = np.load('work/visible_head.npy'); seen = np.load('work/visible_all.npy')
g = np.load('work/groups.npz'); W = g['W']; names = [str(x) for x in g['names']]
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 1; up = c[:, 2] > 1.50
vis = head & np.where(up, seen_h > 0, seen > 0)
FY = float(os.environ.get('M214_FACE_Y', '-0.03'))
front = vis & up & (c[:, 1] < FY)
hv = np.unique(f[head & (c[:, 2] > 1.56)]); axis = v[hv, 0].mean()
ear = head & (np.abs(c[:, 0] - axis) > float(os.environ.get('M214_EAR_X', '0.072'))) & (c[:, 2] > 1.56) & (c[:, 2] < 1.72)
keep = (p == 6) | (hand[f] > 0.3).any(1) | (p == 7) | (p == 12) | small | soles | ear
if os.environ.get('M214_KEEP_FACE', '1') == '1':
    keep |= front
extra = os.environ.get('M214_EXTRA_KEEP')  # e.g. patch or drift-lock sets on top
if extra:
    for x in extra.split(','):
        keep |= np.load(x)
groups = np.zeros(len(f), int)
groups[vis & up] = 2; groups[head & ~vis] = 3; groups[vis & ~up] = 8
for lab, piece in ((4, 2), (5, 8), (6, 10), (7, 13)):
    groups[p == piece] = lab
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face front', int((front & ~((p == 6) | small | ear)).sum()), 'ears', int(ear.sum()), ')',
      {k: int((groups == k).sum()) for k in range(9)}, 'free', int(((groups == 0) & ~keep).sum()))
