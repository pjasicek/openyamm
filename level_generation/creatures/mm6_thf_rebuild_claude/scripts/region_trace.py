#!/usr/bin/env python3
"""Per-frame bad share of one region (motion_audit's rule) split into stretch / squash / fold, and the worst joints. Args: <glb> <clip> <region> [fps]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit as MA
glb, clip, region = sys.argv[1:4]; fps = float(sys.argv[4]) if len(sys.argv) > 4 else 30
a = MA.Audit(glb)
r = MA.REGIONS.index(region)
sel = (a.tri_region == r) & a.valid
tot = a.rest_area[sel].sum()
ts = a.model.clip_times(clip)
for t in np.linspace(ts[0], ts[-1], max(2, int((ts[-1] - ts[0]) * fps) + 1)):
    posed, scale, pal, world = a.pose(clip, t)
    s1, s2, fold, live = a.deformation(posed, scale, pal)
    m = sel & live
    st, sq, fo = m & (s1 > MA.STRETCH), m & (s2 < MA.SQUASH), m & fold
    bad = st | sq | fo
    j = np.bincount(a.tri_joint[bad], a.rest_area[bad], len(a.joint_names))
    top = [(a.joint_names[k], round(100 * j[k] / tot, 1)) for k in np.argsort(-j)[:3] if j[k] > 0]
    print(f'{t:5.2f} bad {100 * a.rest_area[bad].sum() / tot:5.1f}  stretch {100 * a.rest_area[st].sum() / tot:5.1f} squash {100 * a.rest_area[sq].sum() / tot:5.1f} fold {100 * a.rest_area[fo].sum() / tot:5.1f}', top)
