#!/usr/bin/env python3
"""Pick each group's ratio from work/sweep.json: the fewest faces among the rows that pass the checks (closed stays closed,
no new self-intersections, no face turned over, volume 80-120 %) and stay within MAXMM (two-way max, mm) and MEANMM (two-way
mean, mm) at rest and within GAPMM of rest-gap growth to every neighbouring piece; ties go to the lower mean. A group with no
passing row is kept exactly. Hands (gauntlets) not below HAND_MIN (brief: 0.6-0.75). Lined groups count twice (their
lining is rebuilt from the reduced outer faces).
Usage: plan_from_sweep.py <MAXMM> <MEANMM> <out plan.json>  (prints the estimated LOD0 incl. linings and the scimitar)"""
import json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
MAXMM, MEANMM, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
HAND_MIN = float(os.environ.get('HAND_MIN', '0.6'))
GAPMM = float(os.environ.get('GAPMM', '1.0'))
FIXED = {int(k): float(v) for k, v in (kv.split(':') for kv in os.environ.get('FIXED', '').split(',') if kv)}
SW = json.load(open(HERE / 'work' / os.environ.get('SWEEP', 'sweep.json')))
G = np.load(HERE / 'work' / 'groups.npy'); lined = np.load(HERE / 'work' / 'sheet_faces.npy')
mat = (np.load(HERE / 'work' / 'mesh_in.npz')['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
k0 = (G == 0) & (mat != 2)
plan = {}; tot = int(k0.sum()); lin = int((lined & (G == 0)).sum()); cats = {}
for g, e in SW.items():
    cat, n = e['cat'], e['n']
    rows = [r for r in e['rows'] if r[5] and r[3] <= MAXMM and r[4] <= MEANMM and r[7] <= GAPMM]
    if cat == 'hand':
        rows = [r for r in rows if r[0] >= HAND_MIN - 1e-6]
    if int(g) in FIXED:
        rows = [r for r in e['rows'] if r[5] and abs(r[0] - FIXED[int(g)]) < 1e-6][:1]
    if rows:
        best = min(rows, key=lambda r: (r[2], r[4]))
        plan[g] = [best[0], cat, n, best[1]]; k = best[2]
    else:
        plan[g] = [1.0, cat, n, 0]; k = n
    tot += k
    if lined[G == int(g)].any():
        lin += k
    c = cats.setdefault(cat, [0, 0]); c[0] += n; c[1] += k
json.dump(plan, open(out, 'w'))
print(f'MAX {MAXMM} MEAN {MEANMM}: outer {tot} + lining {lin} + scimitar 266 = {tot + lin + 266} ({(tot + lin + 266) / 10484 - 1:+.1%})  ',
      ' '.join(f'{c} {a}->{b}' for c, (a, b) in cats.items()))
