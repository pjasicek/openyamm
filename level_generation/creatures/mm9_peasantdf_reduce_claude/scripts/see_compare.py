#!/usr/bin/env python3
"""See-through summary, installed (creature job 7 runs) vs candidate: worst hole pixels per zone (level / 20 deg) and frames
with holes. Usage: see_compare.py <tag> [designs]"""
import json, sys
tag = sys.argv[1]
for n in (sys.argv[2:] or ['1', '2', '3', '4']):
    try:
        a = json.load(open(f'../mm9_peasantdf_claude/review/gates/job7/see_through_d{n}/st.json'))['summary']
        b = json.load(open(f'review/gates_{tag}/see_through_d{n}/st.json'))['summary']
    except FileNotFoundError as e:
        print(f'd{n}: missing {e.filename}'); continue
    print(f'd{n}: zone: installed max px (lvl/20) frames -> {tag}')
    for z in sorted(set(a) | set(b)):
        f = lambda s: (f"{s['hole_max']:3d} ({s['hole_max_by_elev'].get('0', 0)}/{s['hole_max_by_elev'].get('20', 0)}) {s['frames_with_holes']:3d}f" if s else '  -')
        print(f'   {z:9s} {f(a.get(z))}  ->  {f(b.get(z))}')
