#!/usr/bin/env python3
"""Faces touching the border between two region labels, both sides (MM8 Vampire ankles: the feet at 35 % and the
legs decimated separately folded a step into the right ankle front). Usage: group_border.py <base keep> <out> <a> <b>"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; g = np.load('work/groups.npy'); a, b = int(sys.argv[3]), int(sys.argv[4])
va, vb = np.unique(f[g == a]), np.unique(f[g == b])
border = np.intersect1d(va, vb)
sel = np.isin(g, [a, b]) & np.isin(f, border).any(1)
keep = np.load(sys.argv[1]) | sel; np.save(sys.argv[2], keep)
print('BORDER', len(border), 'verts', int(sel.sum()), 'faces', 'keep', int(keep.sum()))
