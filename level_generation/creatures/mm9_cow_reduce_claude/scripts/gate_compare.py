#!/usr/bin/env python3
"""Installed vs candidate cow gates (review/gates_before vs review/gates_<tag>, scripts/gates.sh): per clip floor min/max (hoof
contact), jitter p99, bone ratio, body-in-body (extra_clip_gates), edge stretch and lowest point (gates.py), fold-overs
(fold_measure.py) and the text gates. Usage: gate_compare.py <tag> -> stdout"""
import json, sys
from pathlib import Path
t = sys.argv[1]; A = Path('review/gates_before'); B = Path(f'review/gates_{t}')


def clipgates(d):
    out = {}
    for line in (d / 'clip_gates.txt').read_text().splitlines():
        parts = line.split(' ', 2)
        if len(parts) == 3 and parts[2].startswith('{'):
            out[parts[1]] = json.loads(parts[2])
    return out


a, b = clipgates(A), clipgates(B)
print('CLIP GATES (floor min/max cm, jitter p99 mm/f2, bone ratio, body-in-body pairs):')
worse = []
for c in a:
    k = lambda z: (z['floor_min_cm'], z['floor_max_cm'], z['jitter_p99_mm_f2'], z['bone_worst_ratio'], z['body_in_body_max_pairs'])
    x, y = k(a[c]), k(b[c])
    print(f'  {c:9s} {x} -> {y}{"" if x == y else "  *"}')
    if y[0] < x[0] - 0.05 or y[2] > x[2] * 1.05 + 0.5 or y[4] > x[4]:
        worse.append(c)
print('  worse beyond noise:', worse or 'none')
ga, gb = json.load(open(A / 'gates.json')), json.load(open(B / 'gates.json'))
print('STRETCH (edge ratio min / max / p1 / p99, lowest, loop seam):')
for c in ga:
    if not isinstance(ga[c], dict) or 'edge_ratio_max' not in ga[c]:
        continue
    k = lambda z: (z['edge_ratio_min'], z['edge_ratio_max'], z['edge_ratio_p1'], z['edge_ratio_p99'], z['lowest'], z.get('loop_seam_max_jump'))
    print(f'  {c:9s} {k(ga[c])} -> {k(gb[c])}')
for f in ('fold.txt', 'detached.txt', 'flat.txt', 'texture_quality.txt', 'winding.txt', 'same_clips.txt'):
    for d in (A, B):
        if (d / f).exists():
            lines = [l.strip() for l in (d / f).read_text().splitlines() if 'Unexpected' not in l and 'RuntimeWarning' not in l]
            if f == 'fold.txt':
                lines = [l[:160] for l in lines if l.startswith(('TOTAL', 'GROUPS'))]
            print(f, d.name, '|', ' / '.join(lines)[:700])
