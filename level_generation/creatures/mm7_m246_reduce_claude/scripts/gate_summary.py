#!/usr/bin/env python3
"""Side-by-side summary of review/gates_<label>.txt (gates.sh) for two labels: G4 arm stretch p99/max per clip, G5 hand
stretch per side, G6 contact depths, head clearance, crest/hair depth, strip stretch, sole range.
Usage: gate_summary.py <label a> <label b>"""
import re, sys
from collections import defaultdict


def parse(label):
    r = defaultdict(dict); skirt_n = defaultdict(int)
    for line in open(f'review/gates_{label}.txt'):
        if m := re.match(r'G4 (\w+):\d+\s+(\w): stretch p99 ([\d.]+) max ([\d.]+)', line):
            k = f'G4 {m[1]} p99/max'; a, b = float(m[3]), float(m[4]); o = r[k].get('v', (0, 0)); r[k]['v'] = (max(o[0], a), max(o[1], b))
        elif m := re.match(r'HANDSTRETCH (\w+)\s+(\w): max ([\d.]+)x', line):
            k = f'G5 hand {m[2]}'; r[k]['v'] = max(r[k].get('v', 0), float(m[3]))
        elif m := re.match(r'G6 (\w+) worst depth cm \(frame, piece hit\): (.*)', line):
            d = eval(m[2]); r[f'G6 {m[1]}']['v'] = {k: v[0] for k, v in d.items() if not k.endswith('_shell')}
        elif m := re.match(r'HEADCLEAR (\w+)\s+deepest ([\d.]+) cm.*closest ([\d.]+) cm', line):
            r[f'head clearance {m[1]} deepest/closest']['v'] = (float(m[2]), float(m[3]))
        elif m := re.match(r'CREST (\w+)\s+(\w+)\s+deepest ([\d.]+)', line):
            k = f'{m[1]} depth max'; r[k]['v'] = max(r[k].get('v', 0), float(m[3]))
        elif m := re.match(r'SKIRT (\w+)\s+max ([\d.]+)x', line):
            skirt_n[m[1]] += 1; k = 'hip panel stretch max' if skirt_n[m[1]] == 1 else 'crest+hair stretch max'
            r[k]['v'] = max(r[k].get('v', 0), float(m[2]))
        elif m := re.match(r'SOLE (\w+): lowest foot per frame min ([-\d.]+) max ([-\d.]+)', line):
            r[f'sole {m[1]} min/max cm']['v'] = (float(m[2]), float(m[3]))
    return {k: v['v'] for k, v in r.items()}


a, b = parse(sys.argv[1]), parse(sys.argv[2])
for k in a:
    print(f'{k:40s} {str(a[k]):45s} {str(b.get(k))}')
