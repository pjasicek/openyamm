#!/usr/bin/env python3
"""Sleeve gate (../mm9_lich_claude/scripts/sleeve_gate.py) json of two runs side by side: per clip, side and view the worst
see-through pixels and frames, and poke frames. Usage: sleeve_compare.py <a.json> <b.json>"""
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
a = a.get('clips', a); b = b.get('clips', b)
worse = 0; tot = [0, 0]
for clip in a:
    for s in ('L', 'R'):
        x, y = a[clip][s], b[clip][s]
        for v in x['see']:
            p, q = x['see'][v]['max_px'], y['see'][v]['max_px']; tot[0] += p; tot[1] += q
            if q > p or y['poke_frames'] > x['poke_frames']:
                worse += 1
                print(f'{clip:14s} {s} {v:6s} see {p:3d} -> {q:3d} px (frames {x["see"][v]["frames"]} -> {y["see"][v]["frames"]}), poke {x["poke_frames"]} -> {y["poke_frames"]}')
print('WORSE entries', worse, '| sum of worst px', tot[0], '->', tot[1],
      '| worst', max(v['max_px'] for c in a.values() for s in 'LR' for v in c[s]['see'].values()), '->',
      max(v['max_px'] for c in b.values() for s in 'LR' for v in c[s]['see'].values()))
