#!/usr/bin/env python3
"""Lowest visible point per key of a clip (floor 0) for a GLB, numpy posing (claude_shared/floor/glb_pose.py).
Usage: death_probe.py <glb> <clip> [step]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); clip = sys.argv[2]; st = int(sys.argv[3]) if len(sys.argv) > 3 else 3
ts = m.clip_times(clip)
low = [(t, m.lowest(clip, float(t))) for t in ts[::st]]
vals = [l[1] if np.isscalar(l[1]) else l[1][0] for l in low]
print('LOW', clip, 'min %.3f at %.2f s, last %.3f' % (min(vals), ts[::st][int(np.argmin(vals))], vals[-1]), ' '.join('%.2f' % v for v in vals))
