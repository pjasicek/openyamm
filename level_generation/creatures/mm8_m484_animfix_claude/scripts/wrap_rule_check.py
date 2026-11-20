#!/usr/bin/env python3
"""Port check of wrap_solve.thigh_rule: the cage fitted to the thigh-following target on an installed clip against the
clip's own cage offsets (world, m; the installed ones also carry the project's skin projection).
    wrap_rule_check.py <glb> <clip>"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_gait  # noqa: E402
import wrap_solve  # noqa: E402

P = compose_gait.Body(sys.argv[1])
clip = sys.argv[2]
S = wrap_solve.setup(P, {})
rule = wrap_solve.thigh_rule(P, S)
T = P.clip_length(clip)
N = int(round(T * 30))
base_local, worlds = P.clip_world(clip, np.arange(N) / N * T)
diff, own, hem = [], [], []
for i in range(N):
    W = worlds[i].copy()
    for node in S['controls']:
        t, _, _ = P.model.rest[node]
        local = base_local[i].get(node, P.model.rest[node])
        W[node] = W[P.parent[node]] @ wrap_solve.glb_pose.trs_matrix(t, local[1], local[2])
    pts = wrap_solve.pose_points(P, W)
    desired, _ = rule(W)
    C = np.linalg.lstsq(S['A'], desired - pts[S['wrap']], rcond=None)[0]
    Ci = np.array([W[P.parent[n]][:3, :3] @ (base_local[i].get(n, P.model.rest[n])[0] - P.model.rest[n][0])
                   for n in S['controls']])
    diff.append(np.linalg.norm(C - Ci, axis=1)); own.append(np.linalg.norm(Ci, axis=1))
    X_rule, X_own = pts[S['wrap']] + S['A'] @ C, pts[S['wrap']] + S['A'] @ Ci
    hem.append(np.linalg.norm(X_rule - X_own, axis=1))
diff, own, hem = map(np.concatenate, (diff, own, hem))
print(f'{clip}: installed control offsets median {np.median(own):.3f} max {own.max():.3f} m; rule fit differs median '
      f'{np.median(diff):.3f} p95 {np.percentile(diff, 95):.3f}; wrap vertices differ median {np.median(hem):.3f} '
      f'p95 {np.percentile(hem, 95):.3f} max {hem.max():.3f} m')
