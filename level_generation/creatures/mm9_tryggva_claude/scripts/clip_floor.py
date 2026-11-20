#!/usr/bin/env python3
"""Lowest and highest visible point (model y, metres; 0 = floor) per clip at its keys, for the script clips the installed
floor audit does not bind (Sit, Agree, Applause, DeadStatic). Usage: clip_floor.py <glb> [clips comma]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
clips = sys.argv[2].split(',') if len(sys.argv) > 2 else list(m.clips)
for c in clips:
    ts = m.clip_times(c)
    lo = [m.lowest(c, float(t)) for t in ts]
    lo = [x[0] if isinstance(x, (tuple, list)) else x for x in lo]
    print(f'{c:12s} lowest min {min(lo):+.3f} max {max(lo):+.3f} over {len(ts)} keys')
