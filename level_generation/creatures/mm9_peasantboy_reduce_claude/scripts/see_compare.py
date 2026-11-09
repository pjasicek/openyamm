#!/usr/bin/env python3
"""See-through summaries side by side: per zone worst hole px (level / 20 deg) and frames with holes, plus per clip worst px.
Usage: see_compare.py <tag a> <tag b>   (review/gates_<tag>/see_through.json)"""
import json, sys
A, B = (json.load(open(f'review/gates_{t}/see_through.json')) for t in sys.argv[1:3])
sa, sb = A.get('summary', A.get('SUMMARY')), B.get('summary', B.get('SUMMARY'))
if sa is None:
    print('keys', list(A)[:10]); sys.exit()
for z in sorted(set(sa) | set(sb)):
    a, b = sa.get(z, {}), sb.get(z, {})
    f = lambda d: f"{d.get('hole_max', 0)} ({d.get('hole_max_by_elev', {}).get('0', 0)}/{d.get('hole_max_by_elev', {}).get('20', 0)}) frames {d.get('frames_with_holes', 0)} worst {d.get('worst')}"
    print(f'{z:10s} {f(a):45s} -> {f(b)}')
