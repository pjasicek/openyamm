#!/usr/bin/env python3
"""Floor contact and height of the installed GLB without a binding (the lane parent writes actors.yml): every key of
every clip posed with claude_shared/floor/glb_pose.py (the floor audit's own posing), lowest and highest point in
model metres, and the standing height for the scale. Args: <glb> [scale]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared', 'floor'))
import glb_pose
glb = sys.argv[1]; scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
m = glb_pose.Model(glb_pose.Glb(glb))
out = {}
for clip in ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Fidget', 'Death', 'Dead'):
    ts = m.clip_times(clip)
    lo = [m.lowest(clip, t) for t in ts]; hi = [m.highest(clip, t) for t in ts]
    out[clip] = {'keys': len(ts), 'lowest_min': round(min(lo), 4), 'lowest_max': round(max(lo), 4),
                 'highest_mean': round(float(np.mean(hi)), 4), 'lowest_last': round(lo[-1], 4)}
    print('PROBE', clip, json.dumps(out[clip]), 'world units x', scale, ': lowest min', round(min(lo) * scale, 2), 'last', round(lo[-1] * scale, 2))
