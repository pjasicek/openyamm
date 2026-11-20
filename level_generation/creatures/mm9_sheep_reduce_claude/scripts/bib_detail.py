#!/usr/bin/env python3
"""Body-in-body detail (extra_clip_gates.py's test) installed vs candidate at given clip frames, with one fixed search radius
(the larger of the two files' 99th-percentile triangle radius x 2, so the count does not move with the triangle size): pair
count, joint pairs and where (rest-pose centroid of the pair's first triangle). Usage: bib_detail.py <inst> <cand> clip:frame ..."""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import extra_clip_gates as X  # noqa: E402
A, B = X.Body(sys.argv[1]), X.Body(sys.argv[2])


def radius(body, V):
    T = body.tris; a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; cen = (a + b + c) / 3
    return np.max(np.stack([np.linalg.norm(x - cen, axis=1) for x in (a, b, c)]), axis=0)


def pairs(body, V, R):
    T = body.tris; a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; cen = (a + b + c) / 3
    rad = radius(body, V); area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    pr = cKDTree(cen).query_pairs(R, output_type='ndarray'); i, j = pr[:, 0], pr[:, 1]
    far = ~body.near[body.tri_joint[i], body.tri_joint[j]]
    shared = (T[i][:, :, None] == T[j][:, None, :]).any(axis=(1, 2))
    ok = far & ~shared & (area[i] > 1e-10) & (area[j] > 1e-10) & (np.linalg.norm(cen[i] - cen[j], axis=1) <= rad[i] + rad[j])
    i, j = i[ok], j[ok]
    hit = X.seg_tri(V, T[i], T[j]) | X.seg_tri(V, T[j], T[i])
    return i[hit], j[hit]


for cf in sys.argv[3:]:
    clip, fr = cf.split(':'); fr = int(fr)
    out = []
    for body in (A, B):
        t = X.frames(body.model, clip, 30)[fr]; V = body.posed(clip, t)[0]; R0 = body.posed(None, 0)[0]
        out.append((body, V, R0))
    R = 2 * max(np.percentile(radius(b, V), 99) for b, V, _ in out)
    for name, (body, V, R0) in zip(('installed', 'candidate'), out):
        i, j = pairs(body, V, R)
        jp = Counter(tuple(sorted((body.names[body.tri_joint[x]], body.names[body.tri_joint[y]]))) for x, y in zip(i, j))
        T = body.tris; c = R0[T[i]].mean(1)
        print(f'{clip}:{fr} {name}: {len(i)} pairs (radius {R * 1000:.1f} mm) {dict(jp)}; rest centroids '
              f'{np.round(c.mean(0), 3) if len(c) else "-"} spread {np.round(c.std(0), 3) if len(c) else "-"}')
