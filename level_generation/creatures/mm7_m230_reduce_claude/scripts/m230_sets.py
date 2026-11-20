#!/usr/bin/env python3
"""Keep set and groups for the m230 ladder (work/regions.npy, soles.npy, mesh_in.npz, groups.npz).
Kept exactly: every face touching a vertex with hand + finger weight > 0.5 (fitted sword grip, grip_check set), small
pieces (<= 80 faces), soles (faces below 6 cm) and the helm front (painted T visor and gold edge: helm faces in front
of the helm centre by more than M230_VISOR_Y, default 0.0 m). Groups: 2 rest of the helm, 3 crest, 4 plume strands, 5 tabard cloth (M230_TEXTILE=<share>: the
heraldry smeared at the body ratio),
label 0 (body plates, gauntlet cuffs, vambraces) takes the ladder budget.
Usage: m230_sets.py <name> [extra keep .npy ...] -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
reg = np.load('work/regions.npy'); soles = np.load('work/soles.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hw = W[:, [i for i, x in enumerate(names) if x.endswith('_Hand') or 'Finger' in x]].sum(1)
hand = (hw[f] > 0.5).any(1)
helm = reg == 2; cy = c[helm][:, 1].mean()
visor = helm & (c[:, 1] < cy - float(os.environ.get('M230_VISOR_Y', '0.0')))
keep = hand | (reg == 8) | soles | visor
for extra in sys.argv[2:]:
    keep |= np.load(extra)
groups = np.zeros(len(f), int)
for r in (2, 3, 4):
    groups[(reg == r) & ~keep] = r
if os.environ.get('M230_TEXTILE'):  # tabard cloth (green/white/red-stained heraldry; textile_frac.npy share of samples)
    textile = (np.load('work/textile_frac.npy') > float(os.environ['M230_TEXTILE'])) & (reg == 1)
    groups[textile & ~keep] = 5
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(hand', int(hand.sum()), 'visor', int(visor.sum()), 'soles', int(soles.sum()), ')',
      {k: int(((groups == k) & ~keep).sum()) for k in (0, 2, 3, 4, 5)})
