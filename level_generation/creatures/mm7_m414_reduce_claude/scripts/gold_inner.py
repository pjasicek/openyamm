#!/usr/bin/env python3
"""Broad gold faces: fully gold faces (work/gold.npy = 1) whose edge neighbours are all fully gold (belt plates,
sandal straps, greave bands) -> work/gold_inner.npy. m414_sets.py (M414_GOLD_INNER=1) lets them into their region's
cut; the gold lines and the borders of gold areas stay kept."""
from collections import defaultdict
import numpy as np
f = np.load('work/mesh_in.npz')['faces']; full = np.load('work/gold.npy') >= 0.99
edges = defaultdict(list)
for i, t in enumerate(f):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        edges[(min(a, b), max(a, b))].append(i)
inner = full.copy()
for fs in edges.values():
    if not all(full[j] for j in fs):
        inner[fs] = False
np.save('work/gold_inner.npy', inner); print('GOLD inner', int(inner.sum()), 'of', int(full.sum()), 'fully gold faces')
