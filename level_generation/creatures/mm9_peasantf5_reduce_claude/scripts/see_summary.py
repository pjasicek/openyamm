#!/usr/bin/env python3
"""Per clip and zone hole_max (and the level / 20 deg split) of see_through.json files side by side.
Usage: see_summary.py <json> [json ...]"""
import json
import sys
D = [json.load(open(p)) for p in sys.argv[1:]]
zones = sorted({z for d in D for c in d['clips'].values() for z in c['zones']})
for clip in D[0]['clips']:
    row = []
    for z in zones:
        vals = [d['clips'].get(clip, {}).get('zones', {}).get(z, {}).get('hole_max', 0) for d in D]
        if any(vals):
            row.append(f"{z} {'/'.join(map(str, vals))}")
    print(f'{clip:9s}', ' | '.join(row))
for z in zones:
    print('MAX', z, '/'.join(str(max(c['zones'].get(z, {}).get('hole_max', 0) for c in d['clips'].values())) for d in D))
