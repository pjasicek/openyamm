"""Lowest point of each clip, metres. Args: glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
for a in m.glb.json['animations']:
    c = a['name']
    ts = np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 30)
    lo = [m.lowest(c, float(t)) for t in ts]
    print(f'{c:13s} lowest {min(lo):.3f} highest {max(lo):.3f}')
