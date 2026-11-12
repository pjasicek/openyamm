#!/usr/bin/env python3
"""The gate's stride measurements (stride_audit: vertices, foot joints) and the floor audit's lowest point range per
clip (model units), for quick candidate iterations.  gate_probe.py <glb> <clip>[,<clip>...]"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/postprocess'))
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402
import stride_audit  # noqa: E402

model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
for clip in sys.argv[2].split(','):
    v, share = stride_audit.measure(model, clip)
    f = stride_audit.measure_feet(model, clip)
    lows = [model.lowest(clip, t) for t in model.clip_times(clip)]
    print(f'{clip:10} vertices {v and round(v, 3)} (contact {share:.2f})  feet {f and round(f, 3)}  '
          f'lowest {100 * min(lows):+.2f}..{100 * max(lows):+.2f} cm')
