#!/usr/bin/env python3
"""Back-side twins (twin_faces.py of the creature: reversed offset copies with the same UVs and weights) of one LOD0 primitive.
A face f is a twin of face o when its corner UVs equal o's reversed (exact float32 bytes), the corresponding corner weights
are equal and the twin's corners lie within 6 mm of o's, behind o (against o's normal). Returns per face: role (0 plain,
1 outer with a twin, 2 twin), the partner face, and the per-corner vertex map outer GLB vertex -> twin GLB vertex."""
import numpy as np


def find_twins(P, UV, W, T):
    uvk = [UV[t].astype(np.float32).tobytes() for t in T]
    rev = {}
    for f, t in enumerate(T):
        for s in range(3):     # all three rotations of the reversed corner order
            r = t[::-1]; r = np.roll(r, s)
            rev.setdefault(UV[r].astype(np.float32).tobytes(), []).append((f, tuple(r)))
    role = np.zeros(len(T), int); partner = -np.ones(len(T), int); vmap = {}
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
    for o, t in enumerate(T):
        for f, r in rev.get(uvk[o], []):
            if f == o or role[f] or role[o] == 2:
                continue
            r = np.array(r)
            d = P[r] - P[t]
            if np.linalg.norm(d, axis=1).max() > 0.006 or np.abs(W[r] - W[t]).max() > 1e-6:
                continue
            if (d @ n[o]).mean() >= 0:
                continue
            role[o] = 1; role[f] = 2; partner[o] = f; partner[f] = o
            for a, b in zip(t, r):
                assert vmap.get(int(a), int(b)) == int(b), 'twin vertex conflict'
                vmap[int(a)] = int(b)
            break
    return role, partner, vmap
