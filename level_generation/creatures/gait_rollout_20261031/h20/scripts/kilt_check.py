#!/usr/bin/env python3
"""Port check of kilt_solve.py: re-solve the kilt controls of an installed clip and compare with its own (offsets of
the controls in world space, m) and the contacts left.  kilt_check.py <glb> <clip> [inside]
With `inside` only the kilt samples left inside the body by the clip's own offsets are counted (every 4th sample)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_gait  # noqa: E402
import kilt_solve  # noqa: E402

P = compose_gait.Body(sys.argv[1])
clip = sys.argv[2]
T = P.clip_length(clip)
N = int(round(T * 120))
base_local, worlds = P.clip_world(clip, np.arange(N) / N * T)
S = kilt_solve.setup(P, {})
only_inside = sys.argv[3:] == ['inside']
report = {}
out = None if only_inside else kilt_solve.solve_kilt(P, worlds, base_local, {}, report)
diff, own, new = [], [], []
for i in range(0 if only_inside else N):
    for node in S['controls']:
        R = worlds[i][P.parent[node]][:3, :3]
        rest = P.model.rest[node][0]
        a = R @ (base_local[i].get(node, P.model.rest[node])[0] - rest)
        b = R @ (out[i][node][0] - rest)
        diff.append(np.linalg.norm(a - b)); own.append(np.linalg.norm(a)); new.append(np.linalg.norm(b))
if not only_inside:
    print(clip, report['kilt_solve'])
    print(f'{clip}: installed offsets median {np.median(own):.3f} max {max(own):.3f} m; re-solved median '
          f'{np.median(new):.3f} max {max(new):.3f}; difference median {np.median(diff):.3f} '
          f'p95 {np.percentile(diff, 95):.3f} max {max(diff):.3f}')
# contacts left by the installed offsets under this criterion (kilt points inside the body)
inside = []
for i in range(0, N, 4):
    W = worlds[i].copy()
    for node in S['controls']:
        t, r, s = P.model.rest[node]
        local = base_local[i].get(node, P.model.rest[node])
        W[node] = W[P.parent[node]] @ kilt_solve.glb_pose.trs_matrix(t, local[1], local[2])
    pts = kilt_solve.pose_points(P, W)
    surface = kilt_solve.Surface(pts, S['body'])
    D = np.array([W[P.parent[n]][:3, :3] @ (base_local[i].get(n, P.model.rest[n])[0] - P.model.rest[n][0])
                  for n in S['controls']])
    _, c = kilt_solve.solve_sample(kilt_solve.samples(S, pts), S['A'], surface, D, {'iterations': 1})
    inside.append(c)
print(f'{clip}: own offsets leave {max(inside)} kilt points inside (max per sample), '
      f'{np.mean(np.array(inside) > 0):.0%} of samples')
