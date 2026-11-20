#!/usr/bin/env python3
"""Spike roots (f90's detached-parts audit: two left elbow spikes parted from the cut skin by 1.0-1.2 cm, a back spike
1.15 -> 1.31 cm): body-skin faces with a vertex within R m of any vertex of a small non-wing piece (spikes, claws, nails;
their roots are sunk into the skin) are kept exactly. Writes work/keep_extra_spike.npy. Usage: spike_keep.py [R]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); nB, nW, nH = (len(p['T']) for p in pr)
s = np.load(HERE / 'work' / 'glb_sets_a.npz'); a = np.load(HERE / 'work' / 'analyse.npz')
P = pr[0]['POSITION'].astype(float); T = pr[0]['T']
wb = s['wingbone'][:nB]; cs = a['csize'][a['prim'] == 0]
small = (cs <= 300) & ~wb; big = (cs > 300) & ~wb
d = cKDTree(P[np.unique(T[small])]).query(P)[0]
keep = big & (d[T] < R).any(1)
print(f'skin faces at spike roots kept {int(keep.sum())}')
np.save(HERE / 'work' / 'keep_extra_spike.npy', np.r_[keep, np.zeros(nW + nH, bool)])
