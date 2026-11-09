#!/usr/bin/env python3
"""Keep set and region groups for the 7m452 Goblin ladder (work/pieces.npy, soles.npy, handw.npy, visible_head.npy).
Kept exactly: both hands (every face touching a vertex with hand + finger weight > 0.3: the billhook grip is solved
per finger), both bracers (thin cuffs over the wrists), the eyes, the mouth, the neck bead, the boot soles (faces below
6 cm), the visible face front (head-piece faces seen in some view, in front of y = FRONT_Y and below the topknot), and
the belt band (skirt-piece faces whose top lies within BELT_H of the skirt's top: a painted strap).
Groups (ratios on the run_ladder.sh line): 1 visible head sides and back (ears, temples, nape), 2 hidden head skin,
3 topknot and crown (head faces above TOP_Z), 4 buckle (dense, 350 faces), 5 trousers, 6 tunic skirt (below the belt),
7 boots, 8 tunic top (torso-piece faces with region mask R > 0.5, filled over the painted button: the printed
pattern tears and flecks under a hard cut, as the Thief's vest), 9 fleece armhole trim (torso-piece faces outside the tunic
mask with bright unsaturated base colour, work/fleece.npy: the rolled rim flattens under a hard cut); label 0 (bare arms
and neck) takes the rest.
Usage: g452_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy   (G452_EXTRA_KEEP=<npy,...> adds patch sets)"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); handw = np.load('work/handw.npy')
seen = np.load('work/visible_head.npy')
FRONT_Y = float(os.environ.get('G452_FRONT_Y', '-0.03')); TOP_Z = float(os.environ.get('G452_TOP_Z', '1.68'))
BELT_H = float(os.environ.get('G452_BELT_H', '0.045'))
head = p == 1; vis = head & (seen > 0); front = vis & (c[:, 1] < FRONT_Y) & (c[:, 2] < TOP_Z)
skirt = p == 3; belt = skirt & (v[f][:, :, 2].max(1) > c[skirt, 2].max() - BELT_H + 0.0)
keep = handw | np.isin(p, [8, 9, 11, 12, 13, 14]) | soles | front | belt
for e in filter(None, os.environ.get('G452_EXTRA_KEEP', '').split(',')):
    keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[vis & ~front] = 1; groups[head & ~vis] = 2; groups[head & (c[:, 2] >= TOP_Z)] = 3
groups[p == 10] = 4; groups[p == 2] = 5; groups[skirt] = 6; groups[np.isin(p, [6, 7])] = 7
rm = np.load('work/regmask.npy'); tunic = (p == 0) & (rm[:, 0] > .5)
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
    tunic = tunic | ((p == 0) & np.array([sum(tunic[j] for j in nb[i]) >= 2 for i in range(len(f))]))
groups[tunic] = 8
fleece = np.load('work/fleece.npy')
for _ in range(1):
    fleece = fleece | ((p == 0) & ~tunic & np.array([sum(fleece[j] for j in nb[i]) >= 2 for i in range(len(f))]))
groups[fleece & ~tunic] = 9
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face front', int((front & keep).sum()), 'belt', int(belt.sum()), 'hands', int(handw.sum()), ')',
      {k: int((groups == k).sum()) for k in range(10)}, 'free', int(((groups == 0) & ~keep).sum()))
