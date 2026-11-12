#!/usr/bin/env python3
"""Per clip: the region's total area and its worst bad area (cm2) over frames, for several GLBs.
    region_area.py <region> <clip,clip> <glb> [<glb> ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
reg = motion_audit.REGIONS.index(sys.argv[1])
for path in sys.argv[3:]:
    a = motion_audit.Audit(path)
    tot = a.rest_area[(a.tri_region == reg) & a.valid].sum() * 1e4
    out = []
    for c in sys.argv[2].split(','):
        ts = a.model.clip_times(c)
        worst = (0, 0)
        for t in np.linspace(ts[0], ts[-1], max(2, int((ts[-1] - ts[0]) * 30) + 1)):
            posed, scale, pal, _ = a.pose(c, t)
            s1, s2, fold, live = a.deformation(posed, scale, pal)
            bad = live & ((s1 > 1.6) | (s2 < 0.55) | fold) & (a.tri_region == reg)
            v = a.rest_area[bad].sum() * 1e4
            if v > worst[0]:
                worst = (v, t)
        out.append(f'{c} {worst[0]:.0f}@{worst[1]:.2f}')
    print(Path(path).name, f'{sys.argv[1]} area {tot:.0f} cm2 |', ' | '.join(out))
