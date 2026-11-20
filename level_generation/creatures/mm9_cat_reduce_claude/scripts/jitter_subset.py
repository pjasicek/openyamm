#!/usr/bin/env python3
"""extra_clip_gates.py's jitter (second difference per vertex, mm/frame^2, 30 fps) on installed and candidate: per clip the
p99 over vertices at the worst frame (the gate number) and the maximum over all vertices, plus the check that every candidate
vertex moves exactly like the installed vertex at the same rest position (so a p99 change is a change of the vertex sample).
Usage: jitter_subset.py <inst> <cand> clip ..."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import extra_clip_gates as X  # noqa: E402
A, B = X.Body(sys.argv[1]), X.Body(sys.argv[2])
ra, rb = A.posed(None, 0)[0], B.posed(None, 0)[0]
d, idx = cKDTree(ra).query(rb)
for clip in sys.argv[3:]:
    acc = []
    for body in (A, B):
        V = np.stack([body.posed(clip, t)[0] for t in X.frames(body.model, clip, 30)])
        acc.append(np.linalg.norm(V[2:] - 2 * V[1:-1] + V[:-2], axis=2) * 1000)
    a, b = acc
    same = np.abs(a[:, idx] - b).max()
    print(f'{clip:12s} p99(worst frame) {np.percentile(a, 99, axis=1).max():.2f} -> {np.percentile(b, 99, axis=1).max():.2f}; '
          f'max over vertices {a.max():.2f} -> {b.max():.2f}; candidate vs same installed vertex max diff {same:.2e} '
          f'(rest match {d.max():.1e} m); vertices {a.shape[1]} -> {b.shape[1]}')
