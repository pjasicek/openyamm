#!/usr/bin/env python3
"""Side-by-side summary of review/gates_<label>.txt: G4 arm stretch p99/max and edge max per side, G5 hand stretch max
per clip and side, G6 worst depths (prop, forearms, hands, prop floor), soles range. Usage: gate_summary.py <label> ..."""
import json, re, sys
for lab in sys.argv[1:]:
    t = open(f'review/gates_{lab}.txt').read()
    g4 = {}
    for side, p99, mx in re.findall(r'G4 \S+\s+([LR]): stretch p99 ([\d.]+) max ([\d.]+)', t):
        a = g4.setdefault(side, [0, 0]); a[0] = max(a[0], float(p99)); a[1] = max(a[1], float(mx))
    g5 = {}
    for clip, side, v in re.findall(r'HANDSTRETCH (\S+)\s+([LR]): max ([\d.]+)x', t):
        g5[side] = max(g5.get(side, 0), float(v))
    g6 = json.load(open(f'work/g6_{lab}.json'))
    worst = {}
    for clip, d in g6.items():
        for k, v in d.items():
            if k.endswith('_shell'):
                continue
            if k == 'prop_floor':
                if v[0] < worst.get(k, (1e9,))[0]:
                    worst[k] = (v[0], clip, v[1])
                continue
            if v[0] > worst.get(k, (-1,))[0]:
                worst[k] = (v[0], clip, v[1], v[2] if len(v) > 2 else None)
    soles = re.findall(r'SOLE (\S+): lowest foot per frame min ([-\d.]+) max ([-\d.]+)', t)
    print(f'== {lab}')
    print('G4 arm stretch p99/max', g4)
    print('G5 hand stretch max', g5)
    print('G6 worst depth cm', worst)
    print('soles cm (min, max of lowest foot)', {c: (float(a), float(b)) for c, a, b in soles})
