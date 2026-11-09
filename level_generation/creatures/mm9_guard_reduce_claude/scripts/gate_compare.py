#!/usr/bin/env python3
"""Before/after of the Guard gates (review/gates_before vs review/gates_<tag>): every changed numeric leaf of the json gates
(collapse, skirt, arm/hand, blade, jitter) and every changed line of the text gates (grip, detached, flat, texture quality, bone
length, winding, same_clips). Usage: gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
import json, sys
t = sys.argv[1]; L = []


def leaves(x, pre=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f'{pre}/{k}')
    elif isinstance(x, list) and all(not isinstance(v, (dict, list)) for v in x) and len(x) <= 8:
        yield pre, x
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f'{pre}[{i}]')
    else:
        yield pre, x


for g in ('collapse', 'skirt', 'arm_hand', 'blade', 'jitter'):
    a = dict(leaves(json.load(open(f'review/gates_before/{g}.json'))))
    b = dict(leaves(json.load(open(f'review/gates_{t}/{g}.json'))))
    ch = [f'  {k}: {a.get(k)} -> {b.get(k)}' for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k) and not k.rsplit('/', 1)[-1].endswith(('frame', 'frame48', 'time')) and '/worst_times/' not in k]
    L.append(f'{g.upper()} changed leaves: {len(ch)}'); L += ch
for g in ('grip', 'detached', 'flat', 'texture_quality', 'bone_length', 'winding', 'same_clips'):
    a = open(f'review/gates_before/{g}.txt').read().splitlines(); b = open(f'review/gates_{t}/{g}.txt').read().splitlines()
    L.append(f'{g.upper()}')
    for x, y in zip(a, b):
        if x != y:
            L.append(f'  - {x[:190]}'); L.append(f'  + {y[:190]}')
    L += [f'  + {y[:190]}' for y in b[len(a):]] + [f'  - {x[:190]}' for x in a[len(b):]]
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
