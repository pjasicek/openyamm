#!/usr/bin/env python3
"""Per-clip before/after of the Monk's collapse, robe and arm/hand gates. Usage: gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
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
a, b = J('robe_gate', 'before'), J('robe_gate', t)
L.append('ROBE (legs through robe frames/max cm, cords under robe frames/max cm)')
for c in a:
    x, y = a[c], b[c]
    if (x['frames'], x['max_cm'], x['cord_frames'], x['cord_cm']) != (y['frames'], y['max_cm'], y['cord_frames'], y['cord_cm']):
        L.append(f"  {c:14s} legs {x['frames']}/{x['of']} {x['max_cm']} -> {y['frames']} {y['max_cm']} | cords {x['cord_frames']} {x['cord_cm']} -> {y['cord_frames']} {y['cord_cm']}")
a, b = J('arm_hand', 'before')['clips'], J('arm_hand', t)['clips']
L.append('ARM/HAND (per side: hand depth cm, frames >1 cm, forearm cm, finger stretch max)')
for c in a:
    for s in a[c]:
        x, y = a[c][s], b[c][s]
        keys = [k for k in x if k != 'hand_frame48' and k != 'forearm_frame48']
        ch = {k: f'{x[k]}->{y[k]}' for k in keys if x[k] != y[k]}
        if ch: L.append(f'  {c:14s} {s} {ch}')
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
