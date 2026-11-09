#!/usr/bin/env python3
"""Walking's floor contact as one smooth low-passed root-height curve (orchestrator 2026-11-04: the walk lifted every foot
3.8 units at one phase after floor_fix.py's grounding + 0.06 s smoothing, whose running maximum biases the curve upward;
per-key grounding failed the jitter gate). Per key the lowest visible point (glb_pose); offsets = -lowest, a cyclic Gaussian
low-pass (SIGMA s, no running maximum), then one constant so the residual lowest point is centred on the floor (as much
sink as lift). Only the root joints' translation keys change (floor_fix.shift_roots).
Usage: walk_floor.py in.glb out.glb [clip Walking] [sigma 0.08]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose
from floor_fix import shift_roots, lowest_series

src, dst = sys.argv[1:3]
clip = sys.argv[3] if len(sys.argv) > 3 else 'Walking'
sigma = float(sys.argv[4]) if len(sys.argv) > 4 else 0.08
glb = glb_pose.Glb(Path(src)); m = glb_pose.Model(glb)
times, lows = lowest_series(m, clip)
body = -lows[:-1]                                   # loop: the last key repeats the first
step = float(np.median(np.diff(times)))
r = int(np.ceil(3 * sigma / step))
k = np.exp(-0.5 * (np.arange(-r, r + 1) * step / sigma) ** 2); k /= k.sum()
sm = np.convolve(np.pad(body, r, mode='wrap'), k, mode='valid')
res = lows[:-1] + sm
sm = sm - 0.5 * (res.max() + res.min())             # centre the residual on the floor
off = np.r_[sm, sm[0]]
shift_roots(m, clip, times, off)
glb.write(Path(dst))
after = lows + off
print(f'WALKFLOOR {clip}: lowest before {lows.min():+.4f}..{lows.max():+.4f}, after {after.min():+.4f}..{after.max():+.4f} m, sigma {sigma}')
