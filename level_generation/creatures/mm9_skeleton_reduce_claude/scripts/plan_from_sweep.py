#!/usr/bin/env python3
"""Pick each group's ratio from work/sweep.json: the fewest faces among the rows that pass the checks and stay within
MAXMM (two-way max, mm) and MEANMM (two-way mean, mm) at rest; ties go to the lower mean. A group with no passing row
is kept exactly (ratio 1). Category caps: HAND_MIN (hands at 0.6-0.75 per the brief: default 0.6), DOME_MIN
(cranium dome, default 0.7). Sheets other than
SHEET_CUT (the back panel) stay exact (their hems are most of their faces).
Usage: plan_from_sweep.py <MAXMM> <MEANMM> <out plan.json>  (prints the estimated LOD0 incl. linings)"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
MAXMM, MEANMM, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
import os
HAND_MIN = float(os.environ.get('HAND_MIN', '0.6'))
# no piece may open its rest gap to a neighbouring piece by more than GAPMM (index knuckles opened 5.8 mm in the first f80)
GAPMM = float(os.environ.get('GAPMM', '1.0'))
# the cranium dome is the skull's silhouette in profile: at 0.4 its back outline showed corners in the viewer (c70)
DOME_MIN = float(os.environ.get('DOME_MIN', '0.7'))
# the rope collar (group 61, 264 faces) and the waist rope (group 45, 230): twisted tubes whose loop outline showed
# corners at 0.5 (d80 chest close-up); ROPE_MIN keeps enough segments round the loop
ROPES = {int(x) for x in os.environ.get('ROPE_GROUPS', '45,61').split(',') if x}
ROPE_MIN = float(os.environ.get('ROPE_MIN', '0.7'))
SW = json.load(open(HERE / 'work' / 'sweep.json'))
G = np.load(HERE / 'work' / 'groups.npy')
sheet_cut = int(os.environ.get('SHEET_CUT_N', '192'))
plan = {}; tot = int((G == 0).sum()); cats = {}
for g, e in SW.items():
    cat, n = e['cat'], e['n']
    rows = [r for r in e['rows'] if r[5] and r[3] <= MAXMM and r[4] <= MEANMM and r[7] <= GAPMM]
    if cat == 'hand':
        rows = [r for r in rows if r[0] >= HAND_MIN - 1e-6]
    if int(g) in ROPES:
        rows = [r for r in rows if r[0] >= ROPE_MIN - 1e-6]
    if cat == 'dome':
        rows = [r for r in rows if r[0] >= DOME_MIN - 1e-6]
    if cat == 'sheet' and n != sheet_cut:
        rows = []
    if rows:
        best = min(rows, key=lambda r: (r[2], r[4]))
        plan[g] = [best[0], cat, n, best[1]]; k = best[2]
    else:
        plan[g] = [1.0, cat, n, 0]; k = n
    tot += k
    c = cats.setdefault(cat, [0, 0]); c[0] += n; c[1] += k
lining = 575 - 192 + (cats.get('sheet', [0, 0])[1] - (cats.get('sheet', [0, 0])[0] - 192))
json.dump(plan, open(out, 'w'))
print(f'MAX {MAXMM} MEAN {MEANMM}: outer {tot} + lining {lining} = {tot + lining}  ', ' '.join(f'{c} {a}->{b}' for c, (a, b) in cats.items()))
