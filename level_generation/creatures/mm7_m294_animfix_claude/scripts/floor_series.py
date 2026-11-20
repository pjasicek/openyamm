#!/usr/bin/env python3
"""Lowest visible point (cm, model units) at every key of clips, as floor_audit.py measures it (all visible meshes).
    floor_series.py <glb> <clip>[,<clip>]"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
from floor_audit import ModelFloor  # noqa: E402
f = ModelFloor(Path(sys.argv[1]))
for clip in sys.argv[2].split(','):
    k = f.keyed(clip)
    lows = [l for _, l in k if l is not None]
    hi = max(k, key=lambda x: x[1])
    print(f'{clip:9s} min {min(lows)*100:+.2f} max {max(lows)*100:+.2f} cm at {hi[0]:.3f}  ' +
          ' '.join(f'{l*100:+.1f}' for _, l in k[::max(1, len(k)//24)]))
