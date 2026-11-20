#!/usr/bin/env python3
"""Collapse gate, installed vs candidate: face-frames per clip and every region whose worst-frame count rose.
Usage: collapse_compare.py <tag> -> prints; reads review/gates_{before,<tag>}/collapse.json"""
import json, sys
a = json.load(open('review/gates_before/collapse.json')); b = json.load(open(f'review/gates_{sys.argv[1]}/collapse.json'))
ta = tb = 0
for c in a:
    ta += a[c]['face_frames']; tb += b[c]['face_frames']
    up = {r: f"{a[c]['worst'].get(r, 0)}->{v}" for r, v in b[c]['worst'].items() if v > a[c]['worst'].get(r, 0)}
    ex = {r: f"{a[c]['exposed_at_worst_frame'].get(r, 0)}->{v}" for r, v in b[c]['exposed_at_worst_frame'].items()
          if v > a[c]['exposed_at_worst_frame'].get(r, 0)}
    print(f"{c:13s} face-frames {a[c]['face_frames']:5d} -> {b[c]['face_frames']:5d}  worst up {up}  exposed up {ex}")
print('TOTAL face-frames', ta, '->', tb)
