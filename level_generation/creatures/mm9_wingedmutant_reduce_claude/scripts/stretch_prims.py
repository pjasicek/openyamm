#!/usr/bin/env python3
"""gates.py's edge stretch split per LOD0 primitive (max over 30 Hz frames of the per-primitive p99 and max ratio), for a
list of clips. Usage: stretch_prims.py <glb> [clip,...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clips = sys.argv[2].split(',') if len(sys.argv) > 2 else list(m.clips)
rest = m.skinned_positions(m.world({})); E, BL = [], []
for pos, t in rest:
    e = np.unique(np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0); E.append(e)
    BL.append(np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1))
for clip in clips:
    ts = m.clip_times(clip); out = []
    for k in range(len(E)):
        p99, mx = 0, 0
        for tt in np.arange(ts[0], ts[-1] + 1e-6, 1 / 30):
            pos = m.skinned_positions(m.world(m.sample(clip, tt)))[k][0]; keep = BL[k] > 1e-4
            r = np.linalg.norm(pos[E[k][:, 0]] - pos[E[k][:, 1]], axis=1)[keep] / BL[k][keep]
            p99 = max(p99, np.percentile(r, 99)); mx = max(mx, r.max())
        out.append(f'{p99:.2f}/{mx:.1f}')
    print(f'{clip:13s} body {out[0]:10s} wing {out[1]:10s} head {out[2]}')
