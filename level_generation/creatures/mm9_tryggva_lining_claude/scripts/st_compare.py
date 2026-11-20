#!/usr/bin/env python3
"""See-through zone maxima of several gate runs side by side (and per clip for the last).
Usage: st_compare.py <tag=json> ... [--clips]"""
import json
import sys
runs = [(a.split('=', 1)[0], json.load(open(a.split('=', 1)[1]))) for a in sys.argv[1:] if '=' in a]
zs = sorted(set().union(*[r['summary'] for _, r in runs]))
print('zone        ' + ' '.join(f'{t:>14s}' for t, _ in runs))
for z in zs:
    print(f'{z:11s} ' + ' '.join(f"{r['summary'].get(z, {}).get('hole_max', 0):14d}" for _, r in runs)
          + f"   worst {runs[-1][1]['summary'].get(z, {}).get('worst')}")
if '--clips' in sys.argv:
    for c, rc in runs[-1][1]['clips'].items():
        print(f'  {c:12s}', {z: v['hole_max'] for z, v in sorted(rc['zones'].items()) if v['hole_max']})
