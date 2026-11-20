#!/usr/bin/env python3
"""Bigfoot gates, installed (review/gates_before) vs candidate (review/gates_<tag>): collapse face-frames and worst-frame
region counts that rose, arm/hand (hand and forearm depth, frames over 1 cm, finger stretch), jitter strict and relative
(fail counts and every changed fail), and the one-line results of the other gates.
Usage: bf_gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
import json, sys
from pathlib import Path
t = sys.argv[1]; L = []
J = lambda f, k: json.load(open(f'review/gates_{k}/{f}.json'))
a, b = J('collapse', 'before'), J('collapse', t)
L.append('COLLAPSE face-frames per clip, worst-frame / exposed region counts that rose')
for c in a:
    up = {r: f"{a[c]['worst'].get(r, 0)}->{v}" for r, v in b[c]['worst'].items() if v > a[c]['worst'].get(r, 0)}
    ex = {r: f"{a[c]['exposed_at_worst_frame'].get(r, 0)}->{v}" for r, v in b[c]['exposed_at_worst_frame'].items()
          if v > a[c]['exposed_at_worst_frame'].get(r, 0)}
    L.append(f"  {c:13s} {a[c]['face_frames']:5d} -> {b[c]['face_frames']:5d}  worst up {up}  exposed up {ex}")
L.append(f"  TOTAL {sum(a[c]['face_frames'] for c in a)} -> {sum(b[c]['face_frames'] for c in b)}")
a, b = J('arm', 'before')['clips'], J('arm', t)['clips']
L.append('ARM/HAND (skin, outer, exact): hand cm / frames>1cm / forearm cm / finger stretch p99,max, where changed')
for c in a:
    for s in 'LR':
        x, y = a[c][s], b[c][s]
        ka = (x['hand_in_body_cm'], x['frames_hand_over_1cm'], x['forearm_in_body_cm'], x['finger_stretch_p99_max'])
        kb = (y['hand_in_body_cm'], y['frames_hand_over_1cm'], y['forearm_in_body_cm'], y['finger_stretch_p99_max'])
        if ka != kb:
            L.append(f'  {c:13s} {s}: {ka} -> {kb}')
L.append(f"  max hand depth {max(a[c][s]['hand_in_body_cm'] for c in a for s in 'LR')} -> {max(b[c][s]['hand_in_body_cm'] for c in b for s in 'LR')} cm; "
         f"frames>1cm {sum(a[c][s]['frames_hand_over_1cm'] for c in a for s in 'LR')} -> {sum(b[c][s]['frames_hand_over_1cm'] for c in b for s in 'LR')}")
for name in ('jitter', 'jitter_rel'):
    a, b = J(name, 'before'), J(name, t)
    fa = sum(a[c][s]['fail'] for c in a for s in 'LR'); fb = sum(b[c][s]['fail'] for c in b for s in 'LR')
    L.append(f'{name.upper()} fails {fa} -> {fb}; changed (shoulder skin excess mm/f2, upper arm / forearm deg/f excess)')
    for c in a:
        for s in 'LR':
            x, y = a[c][s], b[c][s]
            v = lambda z: (z['fail'], z['shoulder_skin']['acc_excess_mm'], z['UpperArm']['angvel_excess'], z['Forearm']['angvel_excess'])
            if v(x) != v(y):
                L.append(f'  {c:13s} {s}: {v(x)} -> {v(y)}')
for f in ('detached', 'flat', 'texture_quality', 'bone_length', 'winding', 'same_clips'):
    for k in ('before', t):
        lines = [l for l in Path(f'review/gates_{k}/{f}.txt').read_text().splitlines() if l.strip() and 'Unexpected' not in l]
        L.append(f'{f.upper()} {k}: ' + ' || '.join(lines[-2:])[:400])
Path(f'review/gates_compare_{t}.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))
