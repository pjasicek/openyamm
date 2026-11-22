#!/usr/bin/env python3
"""Clip gates on an exported GLB (claude_shared/floor/glb_pose.py, the floor audit's own posing):
  - motion: per clip, the skinned vertices' largest per-frame step (cm) and largest acceleration (2nd difference, cm
    per frame^2) as the jerk measure; loops also the seam (last key vs first key, cm; 0 = closed loop);
  - floor: lowest point per clip in world units at the binding scale.
Usage: clip_gates.py <glb> [scale]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as G
path = sys.argv[1]; scale = float(sys.argv[2]) if len(sys.argv) > 2 else 125.0
m = G.Model(G.Glb(path))
LOOPS = {'Standing', 'Walking', 'Running', 'Sprint', 'Dead'}
for clip in m.clips:
    times = m.clip_times(clip)
    P = []
    for t in times:
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        P.append(np.concatenate([pts for pts, _ in posed]))
    P = np.stack(P)
    step = np.linalg.norm(np.diff(P, axis=0), axis=-1).max(1) * 100
    acc = np.linalg.norm(np.diff(P, 2, axis=0), axis=-1).max(1) * 100 if len(P) > 2 else np.zeros(1)
    seam = np.linalg.norm(P[-1] - P[0], axis=-1).max() * 100
    low = P[..., 1].min() * scale   # glTF y up
    print(f'GATE {clip:13s} keys {len(times):3d}  max step {step.max():5.2f} cm  max accel {acc.max():5.2f} cm/f^2'
          f'  seam {seam:5.2f} cm{" (loop)" if clip in LOOPS else ""}  lowest {low:+6.2f} units')
