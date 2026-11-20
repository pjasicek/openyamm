#!/usr/bin/env python3
"""See-through report(s) (see_through_gate.py json) -> per zone: worst hole px over every clip (clip, frame, view) and the number of
clip-frames with holes; a second json side by side. Usage: st_summary.py <a.json> [b.json]"""
import json, sys
R = [json.load(open(p)) for p in sys.argv[1:]]


def zones(r):
    out = {}
    for clip, c in r['clips'].items():
        for z, v in c['zones'].items():
            o = out.setdefault(z, [0, '-', 0])
            if v['hole_max'] > o[0]:
                o[0] = v['hole_max']; o[1] = f"{clip}:{v['worst'][0]}:{v['worst'][1]}" if v['worst'] else clip
            o[2] += len(v['hole_frames'])
    return out


Z = [zones(r) for r in R]
for z in sorted(set().union(*Z)):
    print(f'{z:11s}', ' | '.join(f"{x.get(z, [0, '-', 0])[0]:4d} px {x.get(z, [0, '-', 0])[1]:28s} frames {x.get(z, [0, '-', 0])[2]:4d}" for x in Z))
