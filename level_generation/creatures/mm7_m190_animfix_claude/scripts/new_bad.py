#!/usr/bin/env python3
"""Triangles bad in <after> but not in <before> (any frame, 30 fps) in one region of the before's map, by place.
    new_bad.py <before glb> <after glb> <region> <clip> [<clip> ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
A = motion_audit.Audit(sys.argv[1]); B = motion_audit.Audit(sys.argv[2])
reg = A.tri_region == motion_audit.REGIONS.index(sys.argv[3])
c = A.rest[A.tris].mean(1)
names = A.joint_names
for clip in sys.argv[4:]:
    ts = A.model.clip_times(clip)
    acc = [np.zeros(len(A.tris)), np.zeros(len(A.tris))]
    for t in np.linspace(ts[0], ts[-1], int((ts[-1] - ts[0]) * 30) + 1):
        for i, X in enumerate((A, B)):
            posed, scale, pal, _ = X.pose(clip, t)
            s1, s2, f, live = X.deformation(posed, scale, pal)
            acc[i] = np.maximum(acc[i], (live & ((s1 > 1.6) | (s2 < 0.55) | f)))
    for nm, s in (('new', (acc[1] > 0) & (acc[0] == 0) & reg), ('gone', (acc[0] > 0) & (acc[1] == 0) & reg)):
        print(clip, nm, s.sum(), 'area %.0f cm2' % (A.rest_area[s].sum() * 1e4))
        if s.any():
            j = A.tri_joint[s]
            for k in np.unique(j):
                q = s & (A.tri_joint == k)
                print('   ', names[k], q.sum(), 'area %.0f' % (A.rest_area[q].sum() * 1e4), 'y', np.round(np.percentile(c[q, 1], [0, 50, 100]), 2),
                      'x', np.round(np.percentile(c[q, 0], [0, 50, 100]), 2), 'z', np.round(np.percentile(c[q, 2], [0, 50, 100]), 2))
