#!/usr/bin/env python3
"""Fish head keep set (2026-11-05): body faces of primitive 0 with any vertex in front of Z0 (GLB +z = snout), grown RING rings
-> work/keep_extra_head_p0.npy (read by animal_sets.py EXTRAS=head). Usage: fish_head.py <glb> <z0> [ring]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(sys.argv[1]); z0 = float(sys.argv[2]); ring = int(sys.argv[3]) if len(sys.argv) > 3 else 0
node = next(n for n in doc['nodes'] if n.get('name') == 'Fish' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]; P, T = pr['POSITION'].astype(float), pr['T']
_, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]
sel = (P[T][:, :, 2] > z0).any(1)
for _ in range(ring):
    vm = np.zeros(wv.max() + 1, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1)
np.save(HERE / 'work' / 'keep_extra_head_p0.npy', sel); np.save(HERE / 'work' / 'keep_extra_head_p1.npy', np.zeros(len(gb.prims(doc, b, node['mesh'])[1]['T']), bool)); print('head faces', int(sel.sum()), 'of', len(T))
