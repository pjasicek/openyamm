#!/usr/bin/env python3
"""Shared-gate rows of a candidate against the installed baseline (the installed Pirate already FAILs 488 rows: source
motion ranges, the hook prosthesis palm and distant-LOD fingers). Matches rows by asset/clip/LOD/gate/region; prints
rows that pass in the baseline and not in the candidate, and failing rows whose worst value moved by more than 10 %.
Usage: gate_diff.py <baseline gates.json> <candidate gates.json>"""
import json, sys
load = lambda p: {(r['asset'], r['clip'], r['lod'], r['gate'], r['region']): r for r in json.load(open(p))['gates']}
a, b = load(sys.argv[1]), load(sys.argv[2])
new_fail, worse, better, fixed = [], [], [], []
for k, rb in b.items():
    ra = a.get(k)
    if ra is None:
        if rb['status'] in ('FAIL', 'UNVERIFIED'):
            new_fail.append((k, None, rb))
        continue
    if ra['status'] == 'PASS' and rb['status'] != 'PASS':
        new_fail.append((k, ra, rb))
    elif ra['status'] != 'PASS' and rb['status'] == 'PASS':
        fixed.append(k)
    elif ra['status'] == rb['status'] == 'FAIL' and isinstance(ra['worst'], (int, float)) and isinstance(rb['worst'], (int, float)):
        da, db = abs(ra['worst']), abs(rb['worst'])
        if db > da * 1.1 + 1e-9:
            worse.append((k, ra['worst'], rb['worst']))
        elif db < da * 0.9:
            better.append((k, ra['worst'], rb['worst']))
print('ROWS', len(a), len(b), 'missing', len(set(a) - set(b)))
print('NEW_FAIL', len(new_fail)); [print('  ', k, ra and (ra['status'], ra['worst']), (rb['status'], rb['worst'], rb['threshold'])) for k, ra, rb in new_fail]
print('WORSE_FAIL', len(worse)); [print('  ', k, round(x, 3), '->', round(y, 3)) for k, x, y in worse]
print('BETTER_FAIL', len(better)); [print('  ', k, round(x, 3), '->', round(y, 3)) for k, x, y in better]
print('FIXED', len(fixed)); [print('  ', k) for k in fixed]
