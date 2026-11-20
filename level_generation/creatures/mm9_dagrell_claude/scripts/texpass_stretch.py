#!/usr/bin/env python3
"""Stretch of a Dagrell upload GLB on its own shape (FitPose), own faces only (left limbs have zero UV area): the surface
as painted and as seen. texture_quality.py measures the crouched bind, which pulls joint-spanning pieces apart.
Usage: texpass_stretch.py <upload glb> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import texture_quality as TQ

for path in sys.argv[1:]:
    doc, binary = TQ.read_glb(path)
    p = doc['meshes'][0]['primitives'][0]
    pos = TQ.accessor(doc, binary, p['attributes']['POSITION'])
    uv = TQ.accessor(doc, binary, p['attributes']['TEXCOORD_0'])
    idx = TQ.accessor(doc, binary, p['indices']).astype(int).reshape(-1, 3)
    P, U = pos[idx], uv[idx]
    e1, e2, d1, d2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0], U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    a3 = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    a2 = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    ok = (a2 > 1e-10) & (a3 > 1e-10)
    u = e1 / np.linalg.norm(e1, axis=1, keepdims=True).clip(1e-12)
    n = np.cross(e1, e2)
    v = np.cross(n / np.linalg.norm(n, axis=1, keepdims=True).clip(1e-12), u)
    X = np.stack([np.stack([(e1 * u).sum(1), (e1 * v).sum(1)], 1), np.stack([(e2 * u).sum(1), (e2 * v).sum(1)], 1)], 2)
    Y = np.stack([d1, d2], 2)
    s = np.linalg.svd(Y[ok] @ np.linalg.inv(X[ok]), compute_uv=False)
    r = s[:, 0] / s[:, 1].clip(1e-9)
    w = a3[ok] / a3[ok].sum()
    o = np.argsort(r)
    c = np.cumsum(w[o])
    print(Path(path).name, {f'p{int(q * 100)}': round(float(r[o][np.searchsorted(c, q)]), 2) for q in (.5, .75, .9, .95)},
          {f'over{t}': f'{100 * w[r > t].sum():.1f}%' for t in (1.5, 2, 3, 5)})
