"""Worst value per plate and check over the listed clips of review/armour_gate_<tag>.json (iteration view).
Args: <tag> [tol cm] [clips comma]"""
import json, sys
r = json.load(open(f'review/armour_gate_{sys.argv[1]}.json')); tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else [c for c in r if c != 'Death']
W = {}
for c in clips:
    for n, d in r.get(c, {}).items():
        for k, v in d.items():
            if v[0] > W.get((n[4:], k), [0])[0]:
                W[(n[4:], k)] = [v[0], c, v[1], v[2], v[3] if len(v) > 3 else None]
for (n, k), v in sorted(W.items(), key=lambda x: -x[1][0]):
    if v[0] > tol:
        print(f'{n:12s} {k:16s} {v[0]:5.2f} {v[1]}@{v[2]} {v[3]} {v[4]}')
print('MAX', max([v[0] for v in W.values()] or [0]), 'over', tol, sum(1 for v in W.values() if v[0] > tol))
