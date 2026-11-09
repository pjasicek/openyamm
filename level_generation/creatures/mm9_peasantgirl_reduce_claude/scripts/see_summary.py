#!/usr/bin/env python3
"""Per clip and zone: worst hole pixels at level / at the party's 20 deg (see_through_gate.py json). Usage: see_summary.py <json> [<json> ...]"""
import json, sys
for p in sys.argv[1:]:
    d = json.load(open(p)); print('==', p)
    for c, rc in d['clips'].items():
        row = []
        for z, r in sorted(rc['zones'].items()):
            e = r.get('hole_max_by_elev', {}); row.append(f"{z} " + '/'.join(str(e[k]) for k in sorted(e)) if e else f"{z} {r['hole_max']}")
        print(f'  {c:9s}', ', '.join(row))
