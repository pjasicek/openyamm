#!/usr/bin/env python3
"""Per joint of one motion_audit region: the largest bad share of its own surface over a clip, and when; plus how
much of that region's bad surface sits under the robe (rest height below 0.75 m and within 0.2 m of the body axis).
    region_joints.py <glb> <clip> <region> [fps]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit as ma  # noqa: E402

A = ma.Audit(sys.argv[1]); clip = sys.argv[2]; region = ma.REGIONS.index(sys.argv[3])
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 30
times = A.model.clip_times(clip); n = max(2, int(round((times[-1] - times[0]) * fps)) + 1)
sel = (A.tri_region == region) & A.valid
nj = len(A.joint_names)
total = np.bincount(A.tri_joint[sel], A.rest_area[sel], nj)
best = np.zeros(nj); when = np.zeros(nj)
for t in np.linspace(times[0], times[-1], n):
    posed, scale, palette, _ = A.pose(clip, t)
    s1, s2, fold, live = A.deformation(posed, scale, palette)
    bad = sel & live & ((s1 > ma.STRETCH) | (s2 < ma.SQUASH) | fold)
    share = np.bincount(A.tri_joint[bad], A.rest_area[bad], nj) / np.maximum(total, 1e-20)
    better = share > best; best[better] = share[better]; when[better] = t
for j in np.argsort(-best)[:12]:
    if total[j] > 0:
        print(f'{A.joint_names[j]:16s} bad {100 * best[j]:5.1f} % at {when[j]:.3f} s (area {total[j] * 1e4:.1f} cm2)')
