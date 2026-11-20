"""Compares candidate layouts: atlas use (report), islands, fragment share, stretch p90, face-front chart count and the
largest chart's share of the face front. Usage: layout_stats.py <layout npz>..."""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texture_quality as TQ  # noqa: E402

d = np.load(HERE / 'work' / 'lod0_before.npz')
p, hf = d['piece'], d['head_face']
for path in sys.argv[1:]:
    L = np.load(path)
    uv, xyz = L['uv'], L['xyz']
    rep = json.load(open(path.replace('.npz', '_report.json')))
    isl = TQ.islands(uv, xyz)
    n = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    a3 = np.linalg.norm(n, axis=1) / 2
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    c = xyz.mean(1)
    face = hf & (p == 0) & (n[:, 2] > 0.3) & (c[:, 1] > 1.45)
    cnt = Counter()
    for i in np.nonzero(face)[0]:
        cnt[isl[i]] += a3[i]
    tot = sum(cnt.values())
    sizes = np.bincount(np.unique(isl, return_inverse=True)[1].ravel())
    lab = np.unique(isl, return_inverse=True)[1].ravel()
    frag = a3[sizes[lab] < 8].sum() / a3.sum()
    # stretch: singular value ratio of the UV map per triangle
    e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
    u1, u2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    bx = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    by = np.cross(n, bx)
    P = np.stack([np.stack([(e1 * bx).sum(1), (e1 * by).sum(1)], 1), np.stack([(e2 * bx).sum(1), (e2 * by).sum(1)], 1)], 1)
    U = np.stack([u1, u2], 1)
    ok = np.abs(np.linalg.det(P)) > 1e-12
    J = np.linalg.solve(P[ok], U[ok])
    s = np.linalg.svd(J, compute_uv=False)
    ratio = s[:, 0] / np.maximum(s[:, 1], 1e-12)
    order = np.argsort(ratio)
    cw = np.cumsum(a3[ok][order]) / a3[ok].sum()
    p90 = ratio[order][np.searchsorted(cw, 0.9)]
    print(Path(path).stem, 'use', rep['use'], 'charts', len(sizes), 'fragments %.1f%%' % (100 * frag),
          'stretch p90 %.2f' % p90, 'face-front charts', len(cnt), 'largest %.2f' % (max(cnt.values()) / tot))
