#!/usr/bin/env python3
"""Extra keep faces for set d (see-through fix of c60, scripts/st_probe.py on Dead 0 az045_el00 and Fidget 45 az270_el00: the new
hole pixels hit the shirt skirt between belt and hem, y 0.89-0.99, and the shirt beside the front laces at y 1.29):
shirt faces with a vertex below SKIRT_Y (the skirt under the belt) and shirt faces within PLACKET m of a lace-piece vertex.
-> work/keep_d.npy (per LOD0 face, glb_parts.npz order). Usage: extra_keeps.py"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, D = glbio.load(HERE / 'before' / 'mm9_peasantm1.glb', 'PeasantM1')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; comp = g['comp']
PR = ['PeasantM1_A', 'PeasantM1Head']
P = np.concatenate([D[k]['P'] for k in PR]); T = np.concatenate([D[k]['T'] + g['voff'][i] for i, k in enumerate(PR)])
V = P[T]; SKIRT_Y = float(os.environ.get('SKIRT_Y', '1.02')); PLACKET = float(os.environ.get('PLACKET', '0.05'))
skirt = (part == 1) & (V[:, :, 1].min(1) < SKIRT_Y)
# lace pieces: the two small body pieces in front of the chest (y 1.21-1.46)
lace = np.zeros(len(T), bool)
for c in np.unique(comp[part == 9]):
    m = comp == c; y = V[m][:, :, 1]
    if y.min() > 1.15 and y.max() < 1.5:
        lace |= m
lv = P[np.unique(T[lace])]
placket = (part == 1) & (cKDTree(lv).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < PLACKET)
keep = skirt | placket
print('lace faces', int(lace.sum()), 'skirt', int(skirt.sum()), 'placket', int(placket.sum()), 'total', int(keep.sum()))
np.save(HERE / 'work' / 'keep_d.npy', keep)
