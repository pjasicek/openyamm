#!/usr/bin/env python3
"""Collapse gate, installed vs candidate: face-frames and the worst single-frame count per region, per clip.
Usage: collapse_cmp.py <installed collapse.json> <candidate collapse.json>"""
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
ta = tb = 0
for clip in a:
    x, y = a[clip], b[clip]; ta += x['face_frames']; tb += y['face_frames']
    regs = sorted(set(x['worst']) | set(y['worst']))
    worse = [f"{r} {x['worst'].get(r, 0)}->{y['worst'].get(r, 0)}" for r in regs if y['worst'].get(r, 0) > x['worst'].get(r, 0)]
    print(f"{clip:15s} face-frames {x['face_frames']:5d} -> {y['face_frames']:5d}  worse regions: {', '.join(worse) or '-'}")
print('TOTAL face-frames', ta, '->', tb)
