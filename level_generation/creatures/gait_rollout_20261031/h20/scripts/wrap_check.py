#!/usr/bin/env python3
"""Wrap vertices that need a move (inside the skin, or nearer than 2/3 of the margin) as a clip plays with its own
cage offsets (wrap_solve.py's test), every 2nd sample at 60 Hz.  wrap_check.py <glb> <clip,clip> [margin=0.05]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_gait  # noqa: E402
import wrap_solve  # noqa: E402

P = compose_gait.Body(sys.argv[1])
margin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
S = wrap_solve.setup(P, {'face_samples': True})
for clip in sys.argv[2].split(','):
    T = P.clip_length(clip)
    N = int(round(T * 60))
    base_local, worlds = P.clip_world(clip, np.arange(0, N, 2) / N * T)
    inside, near, deepest = [], [], 0.0
    for i in range(len(worlds)):
        pts = wrap_solve.pose_points(P, worlds[i])
        X = wrap_solve.samples(S, pts)
        tris = tuple(pts[S['skin'][:, k]] for k in range(3))
        surface = wrap_solve.Surface(pts, S['skin'])
        dist, q, nrm = surface.nearest(X)
        facing = np.einsum('ij,ij->i', X - q, nrm)
        cand = np.where((facing < 0) & (dist < 0.25))[0]
        n_in = 0
        if len(cand):
            par = np.isfinite(wrap_solve.ray_hits(X[cand], wrap_solve.PARITY, *tris)).sum(axis=1) % 2 == 1
            n_in = int(par.sum())
            if n_in:
                deepest = max(deepest, float(dist[cand[par]].max()))
        inside.append(n_in)
        near.append(int(((facing >= 0) & (dist < margin * 0.67)).sum()))
    inside = np.array(inside)
    print(f'{clip:9s} wrap vertices inside the skin: {np.mean(inside > 0):4.0%} of samples, most {inside.max()}, '
          f'deepest {deepest * 1000:.0f} mm; within {margin * 0.67 * 1000:.0f} mm outside: most {max(near)}')
