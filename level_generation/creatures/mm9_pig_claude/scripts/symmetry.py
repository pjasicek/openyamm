#!/usr/bin/env python3
"""Mirror symmetry of the bind mesh (largest primitive): mean/max distance of each vertex to the mirror image of the
surface vertices, above a height (legs are staggered in MM9's bind). Usage: symmetry.py <glb> [min height y]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
y0 = float(sys.argv[2]) if len(sys.argv) > 2 else -9
pi = int(np.argmax([len(q['weights']) for q in m.primitives]))
P = m.skinned_positions(m.world({}))[pi][0]
P = P[P[:, 1] > y0]
M = P * np.array([-1, 1, 1])
d = cKDTree(P).query(M)[0]
print(Path(sys.argv[1]).name, 'mirror distance mean %.5f p95 %.5f max %.5f (%d verts)' % (d.mean(), np.percentile(d, 95), d.max(), len(P)))
