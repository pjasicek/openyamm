#!/usr/bin/env python3
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
for a in m.glb.json['animations']:
    n = a['name']; ts = m.clip_times(n); ts = ts[:: max(1, len(ts) // 40)]
    lo = [m.lowest(n, float(t)) for t in ts]; hi = [m.highest(n, float(t)) for t in ts]
    lo = [x[0] if isinstance(x, tuple) else x for x in lo]; hi = [x[0] if isinstance(x, tuple) else x for x in hi]
    print(f'{n:15s} lowest {min(lo):.3f}..{max(lo):.3f}  highest {min(hi):.3f}..{max(hi):.3f}')
