#!/usr/bin/env python3
"""Per clip: lowest/highest point (model units, glTF Y up) over its keys, and the lowest at start/end.
Usage: clip_heights.py <glb> [step_seconds]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Model

from glb_pose import Glb
m = Model(Glb(sys.argv[1]))
step = float(sys.argv[2]) if len(sys.argv) > 2 else 1 / 30
names = [a["name"] for a in m.glb.json["animations"]]
for clip in (names or []):
    times = m.clip_times(clip)
    ts = np.arange(times[0], times[-1] + 1e-6, step)
    lows, highs = [], []
    for t in ts:
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        ys = np.concatenate([p[:, 1] for p, _ in posed])
        lows.append(ys.min()); highs.append(ys.max())
    lows = np.array(lows)
    print(f'{clip:13s} dur {times[-1]:.3f} low {lows.min():+.4f} (t {ts[lows.argmin()]:.2f}) high {max(highs):+.4f} '
          f'start {lows[0]:+.4f} end {lows[-1]:+.4f}')
