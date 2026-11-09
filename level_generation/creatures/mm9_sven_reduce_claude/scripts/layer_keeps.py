#!/usr/bin/env python3
"""Layer keeps (after b65/b75 close-ups: the trousers' crotch showed in front of the tunic's front point, a dark wedge where the
installed tunic tip hangs): faces of the INNER parts whose rest corners come within LAYER m of an OUTER part's vertex.
-> work/keep_layer.npy. Usage: layer_keeps.py  (env LAYER default 0.025, INNER default 5, OUTER default 1; comma lists of parts)"""
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
L = float(os.environ.get('LAYER', '0.025'))
inner = np.isin(part, [int(x) for x in os.environ.get('INNER', '5').split(',')])
outer = np.isin(part, [int(x) for x in os.environ.get('OUTER', '1').split(',')])
d = cKDTree(P[np.unique(T[outer])]).query(P[T].reshape(-1, 3))[0].reshape(-1, 3).min(1)
keep = inner & (d < L)
np.save(HERE / 'work' / 'keep_layer.npy', keep); print('layer keep', int(keep.sum()), 'of inner', int(inner.sum()))
