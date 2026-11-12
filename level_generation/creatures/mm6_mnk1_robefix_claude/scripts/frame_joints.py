#!/usr/bin/env python3
"""At one clip time: per joint of a region, bad share of its own surface split into stretch / squash / fold, and the
mean height of its bad triangles.   frame_joints.py <glb> <clip> <time> [region]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit as ma  # noqa: E402

A = ma.Audit(sys.argv[1]); clip = sys.argv[2]; t = float(sys.argv[3])
region = ma.REGIONS.index(sys.argv[4] if len(sys.argv) > 4 else 'cloth')
posed, scale, palette, _ = A.pose(clip, t)
s1, s2, fold, live = A.deformation(posed, scale, palette)
sel = (A.tri_region == region) & A.valid & live
cent = posed[A.tris].mean(1)
for j in sorted(set(A.tri_joint[sel])):
    m = sel & (A.tri_joint == j); tot = A.rest_area[m].sum()
    st, sq, fo = m & (s1 > ma.STRETCH), m & (s2 < ma.SQUASH), m & fold
    bad = st | sq | fo
    if not bad.any():
        continue
    print(f'{A.joint_names[j]:14s} stretch {100 * A.rest_area[st].sum() / tot:5.1f} squash {100 * A.rest_area[sq].sum() / tot:5.1f} '
          f'fold {100 * A.rest_area[fo].sum() / tot:5.1f}  bad at height {cent[bad, 1].mean():.2f} m (region {cent[m, 1].min():.2f}..{cent[m, 1].max():.2f})')
