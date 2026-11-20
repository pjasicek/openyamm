#!/usr/bin/env python3
"""Kilt samples (kilt_solve.setup: kilt vertices, triangle centroids, edge midpoints) inside the body per clip, as the
clip plays (its own control offsets; env KILT_PREFIX and KILT_TOP for another garment, e.g. Wrap_ and 10): share of
60 Hz samples with any point deeper than 1 cm, the most such points at one sample, and the deepest (mm), with the body
part of the deepest.  kilt_depth_probe.py <glb> <clip,clip>"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import os  # noqa: E402

import compose_gait  # noqa: E402
import kilt_solve  # noqa: E402

P = compose_gait.Body(sys.argv[1])
S = kilt_solve.setup(P, {'prefix': os.environ.get('KILT_PREFIX', 'Skirt_'),
                         'top': float(os.environ.get('KILT_TOP', 0.89))})
names = [n['name'] for n in P.nodes]
prim = P.model.primitives[0]
joints = np.asarray(P.model.joints)
dom = np.array([names[joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(1)]])
for clip in sys.argv[2].split(','):
    T = P.clip_length(clip)
    N = int(round(T * 60))
    _, worlds = P.clip_world(clip, np.arange(N) / N * T)
    deep, most, worst, where = 0, 0, 0.0, Counter()
    for i in range(N):
        pts = kilt_solve.pose_points(P, worlds[i])
        smp = kilt_solve.samples(S, pts)
        surface = kilt_solve.Surface(pts, S['body'])
        d, q, n = surface.nearest(smp)
        depth = -np.einsum('ij,ij->i', smp - q, n)
        hit = (d < 0.15) & (depth > 0.01)
        if hit.any():
            deep += 1
            most = max(most, int(hit.sum()))
            _, tri = surface.tree.query(smp[hit], k=1)
            where.update(dom[S['body'][tri, 0]])
            worst = max(worst, float(depth[hit].max()))
    print(f'{clip:9s} kilt inside >1 cm: {deep / N:4.0%} of samples, most {most} points, deepest {worst * 1000:.0f} mm  '
          f'{dict(where.most_common(3))}')
