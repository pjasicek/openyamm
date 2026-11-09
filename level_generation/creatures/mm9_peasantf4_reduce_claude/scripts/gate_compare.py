#!/usr/bin/env python3
"""Per-clip before/after of PeasantF4's gates (review/gates_before vs review/gates_<tag>): collapse, robe, arm/hand, sleeve poke,
hood/sleeve tube (gate_rt), see-through, flat/detached/winding/bone length lines. Only changes are listed.
Usage: gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
import json, os, sys
t = sys.argv[1]; L = []
J = lambda f, k: json.load(open(f'review/gates_{k}/{f}.json'))
a, b = J('collapse', 'before'), J('collapse', t)
L.append('COLLAPSE (face-frames; worst single-frame region counts that changed, before -> after)')
for c in a:
    wa, wb = a[c]['worst'], b[c]['worst']
    ch = {k: f'{wa.get(k, 0)}->{wb.get(k, 0)}' for k in sorted(set(wa) | set(wb)) if wa.get(k, 0) != wb.get(k, 0)}
    L.append(f"  {c:10s} {a[c]['face_frames']:5d} -> {b[c]['face_frames']:5d}  {ch}")
L.append(f"  TOTAL face-frames {sum(a[c]['face_frames'] for c in a)} -> {sum(b[c]['face_frames'] for c in b)}")
a, b = J('robe_gate', 'before'), J('robe_gate', t)
L.append('ROBE (legs through the robe / cords: frames, cm)')
for c in a:
    if a[c] != b[c]: L.append(f'  {c:10s} {a[c]} -> {b[c]}')
a, b = J('arm_hand', 'before')['clips'], J('arm_hand', t)['clips']
L.append('ARM_HAND (per side: changed fields)')
for c in a:
    for s in a[c]:
        x, y = a[c][s], b[c][s]
        ch = {k: f'{x[k]}->{y[k]}' for k in x if not k.endswith('frame48') and x[k] != y[k]}
        if ch: L.append(f'  {c:10s} {s} {ch}')
a, b = J('sleeve_poke', 'before'), J('sleeve_poke', t)
L.append('SLEEVE_POKE (F1 short sleeve): ' + ('identical' if a == b else f'{a} -> {b}'))
a, b = J('hood_sleeve', 'before'), J('hood_sleeve', t)
L.append('HOOD / SLEEVE TUBE / OLD HOOD (gate_rt: max cm, frames over 1 cm; old hood: frames out)')
for c in a:
    for k in a[c]:
        x, y = a[c][k], b[c][k]
        if (x['max_cm'], x['frames_over_1cm']) != (y['max_cm'], y['frames_over_1cm']):
            L.append(f"  {c:10s} {k:12s} {x['max_cm']} ({x['frames_over_1cm']}/{x['frames']}) -> {y['max_cm']} ({y['frames_over_1cm']}/{y['frames']})")
if os.path.exists(f'review/gates_{t}/see_through.json') and os.path.exists('review/gates_before/see_through.json'):
    a, b = J('see_through', 'before'), J('see_through', t)
    L.append('SEE_THROUGH: before ' + json.dumps(a.get('totals', a.get('summary', '')))[:900])
    L.append('SEE_THROUGH: after  ' + json.dumps(b.get('totals', b.get('summary', '')))[:900])
for f in ('flat', 'detached', 'winding', 'bone_length'):
    x = open(f'review/gates_before/{f}.txt').read().strip().splitlines(); y = open(f'review/gates_{t}/{f}.txt').read().strip().splitlines()
    L.append(f'{f.upper()}: ' + (x[0][:200] if x else '') + '  ->  ' + (y[0][:200] if y else ''))
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
