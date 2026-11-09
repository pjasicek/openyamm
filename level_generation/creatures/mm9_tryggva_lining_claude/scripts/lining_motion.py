#!/usr/bin/env python3
"""Do the lining vertices move like the cloth they line? For every LOD0 vertex past the installed count: its source = the
nearest installed vertex (within 5 mm, rest pose) with the same joints and weights. Per clip at 48 fps: the largest
difference of their second differences (mm/frame^2) and of their posed distance from the rest offset (mm). Equal motion
means the jitter gate's shoulder-skin p95 only moves because the lining copies join its vertex sample.
Usage: lining_motion.py <installed glb> <lined glb> [clips A,B]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
A, B = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else list(B.clips)
pairs = []
for pa, pb in zip(A.primitives, B.primitives):
    n = len(pa['positions']); new = np.arange(n, len(pb['positions']))
    kd = cKDTree(pa['positions'])
    d, idx = kd.query(pb['positions'][new], k=8)
    src = np.full(len(new), -1)
    for i in range(len(new)):
        for dd, j in zip(d[i], idx[i]):
            if dd < 0.005 and np.array_equal(pa['joints'][j], pb['joints'][new[i]]) and \
                    np.allclose(pa['weights'][j], pb['weights'][new[i]]):
                src[i] = j; break
    pairs.append((new, src))
    print(f'prim: {len(new)} lining vertices, {int((src >= 0).sum())} matched to a source vertex')
for clip in clips:
    ts = np.arange(0, max(B.clip_times(clip)) + 1e-6, 1 / 48)
    X = [B.skinned_positions(B.world(B.sample(clip, float(t)))) for t in ts]
    worst_acc, worst_off = 0.0, 0.0
    for k, (new, src) in enumerate(pairs):
        ok = src >= 0
        Pn = np.array([x[k][0][new[ok]] for x in X]); Ps = np.array([x[k][0][src[ok]] for x in X])
        an = np.linalg.norm(Pn[2:] - 2 * Pn[1:-1] + Pn[:-2], axis=2); asr = np.linalg.norm(Ps[2:] - 2 * Ps[1:-1] + Ps[:-2], axis=2)
        worst_acc = max(worst_acc, float(np.abs(an - asr).max()) * 1000)
        off = np.linalg.norm(Pn - Ps, axis=2); worst_off = max(worst_off, float((off - off[0]).max()) * 1000)
    print(f'{clip:12s} lining vs source: second difference differs by at most {worst_acc:.3f} mm/f2, '
          f'offset grows by at most {worst_off:.2f} mm', flush=True)
