#!/usr/bin/env python3
"""Of one region's bad surface per clip sample: share that is stretch (s1 > 1.6), squash (s2 < 0.55) and fold, and the
worst chain level (joint suffix _0.._3).   bad_kind.py <glb> <clip> <region>"""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit as ma  # noqa: E402

A = ma.Audit(sys.argv[1]); clip = sys.argv[2]; region = ma.REGIONS.index(sys.argv[3])
times = A.model.clip_times(clip); n = max(2, int(round((times[-1] - times[0]) * 30)) + 1)
sel = (A.tri_region == region) & A.valid; tot = A.rest_area[sel].sum()
names = np.array(A.joint_names)
for t in np.linspace(times[0], times[-1], n):
    posed, scale, palette, _ = A.pose(clip, t)
    s1, s2, fold, live = A.deformation(posed, scale, palette)
    m = sel & live
    st, sq, fo = m & (s1 > ma.STRETCH), m & (s2 < ma.SQUASH), m & fold
    bad = st | sq | fo
    lv = defaultdict(float)
    for j, a in zip(A.tri_joint[bad], A.rest_area[bad]):
        lv[names[j][-1]] += a
    print(f't {t:.3f} bad {100 * A.rest_area[bad].sum() / tot:5.1f}  stretch {100 * A.rest_area[st].sum() / tot:5.1f} '
          f'squash {100 * A.rest_area[sq].sum() / tot:5.1f} fold {100 * A.rest_area[fo].sum() / tot:5.1f}  by level',
          {k: round(100 * v / tot, 1) for k, v in sorted(lv.items())})
