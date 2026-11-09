#!/usr/bin/env python3
"""Installed vs candidate gate numbers (review/gates_before vs review/gates_<tag>): arm/hand, trident, jitter, stretch, and the
text gates. Usage: gate_compare.py <tag> -> stdout (imp-reduce-20261104)."""
import json, sys
from pathlib import Path
t = sys.argv[1]; A = Path('review/gates_before'); B = Path(f'review/gates_{t}')
ld = lambda d, f: json.load(open(d / f))
a, b = ld(A, 'arm.json')['clips'], ld(B, 'arm.json')['clips']
print('ARM/HAND (hand cm, frames>1cm, forearm cm, finger p99/max, wrist):')
for c in a:
    for s in 'LR':
        x, y = a[c][s], b[c][s]
        k = lambda z: (z['hand_in_body_cm'], z['frames_hand_over_1cm'], z['forearm_in_body_cm'], z['finger_stretch_p99_max'], z['wrist_max_deg'])
        print(f"  {c:12s} {s}: {k(x)} -> {k(y)}{'' if k(x) == k(y) else '  *'}")
a, b = ld(A, 'blade.json'), ld(B, 'blade.json')
print('TRIDENT (worst cm, frames>1cm):')
for c in a:
    print(f"  {c:12s} {a[c]['worst_cm']} / {a[c]['frames_over_1cm']} -> {b[c]['worst_cm']} / {b[c]['frames_over_1cm']}{'' if a[c] == b[c] else '  *'}")
for f in ('jitter.json', 'jitter_extra.json'):
    a, b = ld(A, f), ld(B, f)
    print('JITTER', f, '(shoulder skin excess mm/f2, fail):')
    for c in a:
        for s in 'LR':
            x, y = a[c][s], b[c][s]
            print(f"  {c:12s} {s}: {x['shoulder_skin']['acc_excess_mm']} {x['fail']} -> {y['shoulder_skin']['acc_excess_mm']} {y['fail']}"
                  f"{'' if (x['shoulder_skin']['acc_excess_mm'], x['fail']) == (y['shoulder_skin']['acc_excess_mm'], y['fail']) else '  *'}")
a, b = ld(A, 'stretch.json'), ld(B, 'stretch.json')
print('STRETCH (edge ratio min / max / p99, lowest):')
for c in a:
    if not isinstance(a[c], dict) or 'edge_ratio_max' not in a[c]:
        continue
    k = lambda z: (z['edge_ratio_min'], z['edge_ratio_max'], z['edge_ratio_p99'], z['lowest'])
    print(f"  {c:12s} {k(a[c])} -> {k(b[c])}")
for f in ('detached.txt', 'flat.txt', 'texture_quality.txt', 'bone_length.txt', 'winding.txt', 'same_clips.txt'):
    for d in (A, B):
        if (d / f).exists():
            print(f, d.name, '|', ' / '.join(l.strip() for l in (d / f).read_text().splitlines() if 'Unexpected' not in l)[:600])
