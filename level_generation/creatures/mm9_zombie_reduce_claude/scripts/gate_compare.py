#!/usr/bin/env python3
"""Per-clip before/after of the Zombie's gates (review/gates_before vs review/gates_<tag>): collapse, cloth, arm/hand,
jitter; only clips that changed are listed. Usage: gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
import json, sys
t = sys.argv[1]; L = []
J = lambda f, k: json.load(open(f'review/gates_{k}/{f}.json'))
a, b = J('collapse', 'before'), J('collapse', t)
L.append('COLLAPSE (face-frames; worst single-frame region counts that changed, before -> after)')
for c in a:
    wa, wb = a[c]['worst'], b[c]['worst']
    ch = {k: f'{wa.get(k, 0)}->{wb.get(k, 0)}' for k in sorted(set(wa) | set(wb)) if wa.get(k, 0) != wb.get(k, 0)}
    L.append(f"  {c:14s} {a[c]['face_frames']:5d} -> {b[c]['face_frames']:5d}  {ch}")
L.append(f"  TOTAL face-frames {sum(a[c]['face_frames'] for c in a)} -> {sum(b[c]['face_frames'] for c in b)}")
a, b = J('cloth', 'before'), J('cloth', t)
L.append('CLOTH (thigh vertices through the tatter: frames/of, max cm)')
for c in a:
    x, y = a[c], b[c]
    if (x['frames'], x['max_cm']) != (y['frames'], y['max_cm']):
        L.append(f"  {c:14s} {x['frames']}/{x['of']} {x['max_cm']} -> {y['frames']}/{y['of']} {y['max_cm']}")
for g in ('arm_hand',):
    a, b = J(g, 'before')['clips'], J(g, t)['clips']
    L.append(f'{g.upper()} (per side: changed fields)')
    for c in a:
        for s in a[c]:
            x, y = a[c][s], b[c][s]
            ch = {k: f'{x[k]}->{y[k]}' for k in x if not k.endswith('frame48') and x[k] != y[k]}
            if ch: L.append(f'  {c:14s} {s} {ch}')
for g in ('jitter',):
    a, b = open(f'review/gates_before/{g}.txt').read().strip().splitlines()[-1], open(f'review/gates_{t}/{g}.txt').read().strip().splitlines()[-1]
    L.append(f'JITTER last line: {a} -> {b}')
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
