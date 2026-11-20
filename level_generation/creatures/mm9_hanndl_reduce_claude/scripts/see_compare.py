#!/usr/bin/env python3
"""See-through gate before/after: per zone the worst hole pixels over every clip (and where) and the frames with any hole.
Usage: see_compare.py <before json> <after json>"""
import json, sys
A, B = (json.load(open(p)) for p in sys.argv[1:3])
def zones(r):
    out = {}
    for c, rc in r['clips'].items():
        for z, d in rc['zones'].items():
            o = out.setdefault(z, {'max': 0, 'at': '', 'frames': 0})
            o['frames'] += len(d.get('hole_frames', []))
            if d['hole_max'] > o['max']:
                o['max'] = d['hole_max']; o['at'] = c
    return out
za, zb = zones(A), zones(B)
for z in sorted(set(za) | set(zb)):
    a, b = za.get(z, {'max': 0, 'at': '', 'frames': 0}), zb.get(z, {'max': 0, 'at': '', 'frames': 0})
    print(f"{z:12s} worst px {a['max']:5d} ({a['at']}) -> {b['max']:5d} ({b['at']})   frames with holes {a['frames']:4d} -> {b['frames']:4d}")
print('sum of zone maxima', sum(v['max'] for v in za.values()), '->', sum(v['max'] for v in zb.values()))
