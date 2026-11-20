#!/usr/bin/env python3
"""Installed vs candidate gate JSONs (scripts/gates.sh outputs): one line per clip and measure where the candidate is worse.
Usage: gate_compare.py <installed tag> <candidate tag>  (review/gates_<tag>/)"""
import json
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'review'
a, b = sys.argv[1:3]
J = lambda t, f: json.loads((R / f'gates_{t}' / f'{f}.json').read_text())
worse = []


def cmp(gate, clip, key, x, y, tol=0.0):
    if y > x + tol:
        worse.append(f'{gate:9s} {clip:14s} {key:28s} {x} -> {y}')


A, B = J(a, 'collapse'), J(b, 'collapse')
for c in A:
    cmp('collapse', c, 'face_frames', A[c]['face_frames'], B[c]['face_frames'], 0)
    for k in set(A[c]['worst']) | set(B[c]['worst']):
        cmp('collapse', c, f'worst {k}', A[c]['worst'].get(k, 0), B[c]['worst'].get(k, 0), 1)
A, B = J(a, 'cloth'), J(b, 'cloth')
for c in A:
    for k in A[c]:
        cmp('cloth', c, f'{k} frames', A[c][k]['frames'], B[c][k]['frames']); cmp('cloth', c, f'{k} cm', A[c][k]['worst_cm'], B[c][k]['worst_cm'], 0.1)
A, B = J(a, 'arm_hand')['clips'], J(b, 'arm_hand')['clips']
for c in A:
    for s in A[c]:
        for k in ('hand_in_body_cm', 'frames_hand_over_1cm', 'forearm_in_body_cm'):
            cmp('arm_hand', c, f'{s} {k}', A[c][s][k], B[c][s][k], 0.1 if 'cm' in k else 0)
A, B = J(a, 'grip'), J(b, 'grip')
for c in A:
    for k in ('inside_cm', 'skin_inside_cm', 'palm_gap_p10_cm'):
        cmp('grip', c, k, A[c][k], B[c][k], 0.05)
    cmp('grip', c, 'wrap_deg (lower)', -A[c]['wrap_deg'], -B[c]['wrap_deg'], 2)
A, B = J(a, 'staff'), J(b, 'staff')
for c in A:
    cmp('staff', c, 'frames_behind', A[c]['frames_behind'][0], B[c]['frames_behind'][0], 1)
    cmp('staff', c, 'most_behind', A[c]['most_behind'], B[c]['most_behind'], 1)
A, B = J(a, 'jitter'), J(b, 'jitter')
for c in A:
    for s in ('L', 'R'):
        for k in A[c][s]:
            if isinstance(A[c][s][k], (int, float)) and 'frame' not in k and 'ref' not in k:
                cmp('jitter', c, f'{s} {k}', A[c][s][k], B[c][s][k], 0.05)
print('\n'.join(worse) if worse else 'no gate worse')
for f in ('flat', 'winding', 'bone_length', 'same_clips', 'staff_head'):
    for t in (a, b):
        p = R / f'gates_{t}' / f'{f}.txt'
        if p.exists():
            lines = [x for x in p.read_text().split('\n') if x.strip()]
            print(f'{f:12s} {t:10s}', ' | '.join(lines[-2:])[:300])
for t in (a, b):
    p = R / f'gates_{t}' / 'detached.txt'
    if p.exists():
        print('detached', t, ' '.join(x for x in p.read_text().split('\n') if 'detached' in x.lower())[:400])
