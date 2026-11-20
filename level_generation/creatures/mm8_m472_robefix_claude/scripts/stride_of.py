#!/usr/bin/env python3
"""Stride of one clip of a GLB as stride_audit.py measures it (vertices and foot joints), its length and the authored
speed.  stride_of.py <glb> <clip> [<clip> ...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/postprocess'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
import glb_pose  # noqa: E402
import stride_audit  # noqa: E402

model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
for clip in sys.argv[2:]:
    length = model.clip_times(clip)[-1]
    measured, share = stride_audit.measure(model, clip)
    feet = stride_audit.measure_feet(model, clip)
    print(f'{clip}: length {length:.3f} s, stride vertices {measured:.3f} (contact {share:.0%}), feet {feet:.3f}, '
          f'speed {measured / length:.2f} m/s')
