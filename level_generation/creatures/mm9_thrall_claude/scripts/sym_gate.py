#!/usr/bin/env python3
"""Mirror residual of the rest skin below the neck, arms and legs excluded (their bind differs on purpose: MM9's own bind is asymmetric), ours and MM9's."""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
for p, lo, hi in (('work/quick_clips.glb', 0.84, 1.5), ('source/true/thrall1_true.glb', 0.0, 0.62)):
    m = Model(Glb(p)); P = np.concatenate([r[0] for r in m.skinned_positions(m.world({}))])
    q = P[(P[:, 1] > lo) & (P[:, 1] < hi) & (np.abs(P[:, 0]) < 0.2)]
    x0 = np.median(q[:, 0]); a = q - [x0, 0, 0]; d = cKDTree(a).query(a * [-1, 1, 1])[0]
    print(p, len(q), 'p95 mm', round(float(np.percentile(d, 95) * 1000), 1), 'max', round(float(d.max() * 1000), 1))
