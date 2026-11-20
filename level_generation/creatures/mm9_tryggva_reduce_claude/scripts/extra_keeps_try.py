#!/usr/bin/env python3
"""Extra keep mask after the a55 close-ups (belt top edge and buckle smeared dark wedges; dark smear on the tunic above the
buckle): the belt (part 3) whole and every body face within BELT m of a belt vertex -> work/keep_belt.npy."""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio, cfg  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / cfg.GLB, cfg.NODE)
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
P = np.concatenate([D[k]['P'] for k in cfg.PR]); T = np.concatenate([D[k]['T'] + g['voff'][i] for i, k in enumerate(cfg.PR)])
belt = part == 3
d = cKDTree(P[np.unique(T[belt])]).query(P[T].reshape(-1, 3))[0].reshape(-1, 3).min(1)
keep = belt | ((g['mat'] == 0) & (d < float(os.environ.get('BELT', '0.02'))))
np.save(HERE / 'work' / 'keep_belt.npy', keep); print('keep_belt', int(keep.sum()), 'belt', int(belt.sum()))
