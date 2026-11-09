#!/usr/bin/env python3
"""Summarise see_through.json files side by side: per zone the worst hole px over all clips (level / 20 deg) and its clip/frame/view.
Usage: see_summary.py <json> [<json> ...]"""
import json, sys
R = [json.load(open(p)) for p in sys.argv[1:]]
def zones(r):
    out = {}
    for clip, cd in r['clips'].items():
        for z, v in cd['zones'].items():
            if not isinstance(v, dict) or 'hole_max' not in v:
                continue
            o = out.setdefault(z, {'max': 0, 'at': None, 'frames': 0, 'el20': 0})
            o['el20'] = max(o['el20'], v.get('hole_max_by_elev', {}).get('20', 0))
            o['frames'] += len(v.get('hole_frames', []))
            if v['hole_max'] > o['max']:
                o['max'] = v['hole_max']; o['at'] = (clip, v.get('worst'))
    return out
Z = [zones(r) for r in R]
for z in sorted(set().union(*[set(x) for x in Z])):
    print(f'{z:10s}', ' | '.join(f"max {x.get(z, {}).get('max', 0):5d}/{x.get(z, {}).get('el20', 0):3d} frames {x.get(z, {}).get('frames', 0):4d} at {x.get(z, {}).get('at')}" for x in Z))
