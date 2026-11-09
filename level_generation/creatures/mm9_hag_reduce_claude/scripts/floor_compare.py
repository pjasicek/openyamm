#!/usr/bin/env python3
"""Floor contact before/after: per clip, the lowest visible LOD0 point (cm, glTF y) over every key, min and max, for the installed and
the reduced GLB (the clips are the same bytes, so any difference is geometry). Usage: floor_compare.py <installed glb> <reduced glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
A, B = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2])); worst = 0.0
for clip in A.clips:
    t = A.clip_times(clip)
    a = np.array([A.lowest(clip, x) for x in t]) * 100; b = np.array([B.lowest(clip, x) for x in t]) * 100
    worst = max(worst, float(np.abs(a - b).max()))
    print(f'{clip:14s} installed {a.min():+.2f}..{a.max():+.2f}  reduced {b.min():+.2f}..{b.max():+.2f}  max diff {np.abs(a - b).max():.2f} cm')
print('FLOOR max difference', round(worst, 2), 'cm')
