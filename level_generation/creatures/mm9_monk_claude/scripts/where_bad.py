#!/usr/bin/env python3
"""Where the collapsed faces sit in the bind (z rows, azimuth). Args: glb clip time"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clip = sys.argv[2]; t = float(sys.argv[3])
PR = m.primitives; rest = np.vstack([np.asarray(p['positions'], float) for p in PR]); OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
P = np.vstack([x[0] for x in m.skinned_positions(m.world(m.sample(clip, t)))])
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); n, a = tri(P)
c = rest[T].mean(1)
r = a / np.maximum(a0, 1e-12); bad = (r < 0.2) & (a0 > 1e-9)
print('bad', bad.sum(), 'area small p', np.percentile(a0, [5, 50, 95]))
h, e = np.histogram(c[bad, 1], bins=np.arange(-0.1, 1.9, 0.1)); print('height hist', list(zip(e.round(1).tolist(), h.tolist())))
print('edge lens bad p50', np.percentile(np.linalg.norm(rest[T[bad, 0]] - rest[T[bad, 1]], axis=1), 50), 'all', np.percentile(np.linalg.norm(rest[T[:, 0]] - rest[T[:, 1]], axis=1), 50))
# stretch: max/min edge ratio
