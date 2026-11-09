#!/usr/bin/env python3
"""See-through gate before vs candidate: per clip and zone hole_max (px) and hole frame count. Usage: see_through_compare.py <tag>"""
import json, sys
a = json.load(open('review/gates_before/see_through.json'))['clips']; b = json.load(open(f'review/gates_{sys.argv[1]}/see_through.json'))['clips']
same = True
for c in a:
    for z in sorted(set(a[c]['zones']) | set(b[c]['zones'])):
        za, zb = a[c]['zones'].get(z, {}), b[c]['zones'].get(z, {})
        ha, hb = za.get('hole_max', 0), zb.get('hole_max', 0); fa, fb = len(za.get('hole_frames', [])), len(zb.get('hole_frames', []))
        if ha or hb:
            flag = '' if (ha, fa) == (hb, fb) else '  CHANGED'; same &= not flag
            print(f'{c:12s} {z:9s} {ha:3d} px {fa:2d} frames -> {hb:3d} px {fb:2d} frames{flag}')
print('IDENTICAL' if same else 'DIFFERS')
