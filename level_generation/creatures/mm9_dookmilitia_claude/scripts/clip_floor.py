"""Lowest visible point per clip at every key and at 48 fps (diagnosis, model units, cm): clip_floor.py <glb> [clips,..]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); want = sys.argv[2].split(',') if len(sys.argv) > 2 else list(m.clips)
for c in want:
    T = sorted(set(np.round(list(m.clip_times(c)), 5)) | set(np.round(np.arange(0, max(m.clip_times(c)) + 1e-6, 1 / 48), 5)))
    lows = []
    for t in T:
        lows.append(float(m.lowest(c, float(t))))
    lows = np.array(lows) * 100
    print(f'{c:13s} min {lows.min():6.2f} cm max-of-min {lows.max():6.2f}  series', np.round(lows[::max(1, len(lows) // 12)], 1))
