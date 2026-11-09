#!/usr/bin/env python3
"""Posed deviation of a candidate's LOD0 from the installed one: per clip at 48 fps, every candidate vertex's distance to the
installed posed surface (same primitive), max and where (dominant joint). Finds weight errors a rest-pose measure misses.
Usage: pose_dev.py <installed.glb> <candidate.glb> [clips,...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
A, B = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else list(A.clips)
names = [A.glb.json['nodes'][j].get('name') for j in A.joints]
pb = B.primitives
import os
K = int(os.environ.get("K", "48"))
for clip in clips:
    worst = (0, None)
    for t in np.arange(0, A.clip_times(clip)[-1] + 1e-6, 1 / 48):
        xa = A.skinned_positions(A.world(A.sample(clip, float(t)))); xb = B.skinned_positions(B.world(B.sample(clip, float(t))))
        for pi in (0, 1):
            Pa, Ta = xa[pi]; Pb, _ = xb[pi]
            cen = Pa[Ta].mean(1); _, nn = cKDTree(cen).query(Pb, k=K)
            pts = np.repeat(Pb, K, 0); f = nn.ravel()
            q, _ = closest_on_triangles(pts, Pa[Ta[f, 0]], Pa[Ta[f, 1]], Pa[Ta[f, 2]])
            d = np.linalg.norm(q - pts, axis=1).reshape(-1, K).min(1)
            i = int(d.argmax())
            if d[i] > worst[0]:
                j = pb[pi]['joints'][i][pb[pi]['weights'][i].argmax()]
                worst = (float(d[i]), f'{t:.3f}s prim{pi} v{i} {names[j]}')
    print(f'{clip:15s} max {worst[0] * 1000:6.1f} mm at {worst[1]}', flush=True)
