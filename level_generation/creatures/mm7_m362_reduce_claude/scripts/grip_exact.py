#!/usr/bin/env python3
"""grip_check.py follow-up: a hand vertex whose nearest reduced vertex has other weights may sit on a coincident pair
(two source vertices at one position with different weights, e.g. adjacent finger pieces). Counts the hand vertices
with NO reduced vertex at the same position (< 0.01 mm) carrying the same weights. Usage: grip_exact.py <src> <red> <node>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = sys.argv[:4]
import grip_check as G  # noqa: E402  (prints the plain check first)
sp, sw, names = G.lod0(sys.argv[1]); cp, cw, _ = G.lod0(sys.argv[2])
hand = sw[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or any(k in n for k in G.FINGERS)]].sum(1) > .5
t = cKDTree(cp); bad = 0
for i in np.where(hand)[0]:
    if not any(np.abs(sw[i] - cw[j]).max() < 0.002 for j in t.query_ball_point(sp[i], 1e-5)):
        bad += 1; print('NOMATCH', i, np.round(sp[i], 4), [names[k] for k in np.nonzero(sw[i])[0]])
pairs = [p for p in cKDTree(sp).query_pairs(1e-6) if np.abs(sw[p[0]] - sw[p[1]]).max() > 0.002]
print('GRIPEXACT hand vertices without an exact match:', bad, '| source coincident pairs with other weights:', len(pairs))
