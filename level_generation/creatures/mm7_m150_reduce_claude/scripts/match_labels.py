#!/usr/bin/env python3
"""Master labels onto the source faces (work/mesh_in.npz order): nearest master face centroid -> work/src_labels.npz
(piece, garment, head per source face) and the match distance. Usage: python3 match_labels.py"""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); m = np.load('work/master_faces.npz')
cen = d['verts'][d['faces']].mean(1)
dist, idx = cKDTree(m['centroid']).query(cen)
np.savez('work/src_labels.npz', piece=m['piece'][idx], garment=m['garment'][idx], head=m['head'][idx], dist=dist)
print('MATCH faces', len(cen), 'centroid distance mm p50/p99/max', *np.round(np.percentile(dist, [50, 99, 100]) * 1000, 2))
for g in range(9):
    print('  garment', g, int((m['garment'][idx] == g).sum()))
