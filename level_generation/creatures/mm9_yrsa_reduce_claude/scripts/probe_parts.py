#!/usr/bin/env python3
"""Yrsa: match installed GLB triangles to the master (work/master_labels.npz of mm9_yrsa_claude/v2/work/sleeves_v2.blend),
find the frame offset, list connected pieces per prim with master hand/head flags."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yrsa.glb', 'Yrsa')
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
m = np.load(HERE / 'work' / 'master_labels.npz')
mc = m['cen'].astype(float)
for name in ('Yrsa', 'YrsaHead'):
    P, T = D[name]['P'], D[name]['T']
    cen = P[T].mean(1); cb = np.c_[cen[:, 0], -cen[:, 2], cen[:, 1]]
    off = np.median(mc, 0) - np.median(cb, 0) if name == 'Yrsa' else off
    print(name, len(T), 'P lo', P.min(0).round(3), 'hi', P.max(0).round(3))
    print('offset guess', off.round(4))
