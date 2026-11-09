#!/usr/bin/env python3
"""Deformation and loop gates of the wolf's mm9_wolf_claude/scripts/gates.py for the given clips of a GLB (that script
gates every clip and knows only Standing/Walking/Running as loops): edge ratio posed/bind (p1, p99, min, max), the
lowest point, and the loop seam (largest vertex jump between the last and the first sample, model units), plus each
clip's seam against the same clip one 60 Hz step in (the motion of a normal step, for scale).

    trot_gates.py <glb> <clip>[,<clip>...]
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
from glb_pose import Glb, Model  # noqa: E402

m = Model(Glb(sys.argv[1]))
rest = m.skinned_positions(m.world({}))
edges, bind = [], []
for pos, tris in rest:
    t = np.asarray(tris).reshape(-1, 3)
    e = np.unique(np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    edges.append(e)
    bind.append(np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1))
for clip in sys.argv[2].split(","):
    times = m.clip_times(clip)
    ts = np.arange(times[0], times[-1] + 1e-6, 1 / 60)
    rmin, rmax, p1, p99, low, frames = 9, 0, [], [], 1e9, []
    for tt in ts:
        posed = m.skinned_positions(m.world(m.sample(clip, tt)))
        for k, (pos, _) in enumerate(posed):
            keep = bind[k] > 1e-4
            r = np.linalg.norm(pos[edges[k][:, 0]] - pos[edges[k][:, 1]], axis=1)[keep] / bind[k][keep]
            rmin, rmax = min(rmin, r.min()), max(rmax, r.max())
            p1.append(np.percentile(r, 1)); p99.append(np.percentile(r, 99))
            low = min(low, pos[:, 1].min())
        frames.append(np.concatenate([p for p, _ in posed]))
    seam = float(np.linalg.norm(frames[-1] - frames[0], axis=1).max())
    step = float(np.median([np.linalg.norm(frames[k + 1] - frames[k], axis=1).max() for k in range(len(frames) - 1)]))
    print(f"{clip}: edge ratio p1 {min(p1):.3f} p99 {max(p99):.3f} min {rmin:.3f} max {rmax:.3f}  lowest {low * 100:+.2f} cm"
          f"  loop seam {seam:.4f} (median step {step:.4f})")
