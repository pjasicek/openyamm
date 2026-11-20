#!/usr/bin/env python3
"""Add the suit's sleeve ends to a keep set: every face touching a vertex with hand + finger weight > 0.3
(work/groups.npz). Without it 45 hand-weighted sleeve vertices beside the gloves moved up to 9.8 mm.
Usage: cuff_keep.py <base keep .npy> <out .npy>"""
import sys
import numpy as np
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names']); f = np.load('work/mesh_in.npz')['faces']
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= (hand[f] > 0.3).any(1)
np.save(sys.argv[2], keep); print('CUFF keep', n0, '->', int(keep.sum()))
