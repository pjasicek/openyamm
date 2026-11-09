#!/usr/bin/env python3
"""Per-clip before/after of the Honk female's gates (review/gates_before vs review/gates_<tag>): collapse, robe, hair, arm/hand,
jitter, sleeve, forearm poke and the one-line audits; only clips that changed are listed.
Usage: gate_compare.py <tag> -> review/gates_compare_<tag>.txt"""
import json, sys
from pathlib import Path
t = sys.argv[1]; L = []
J = lambda f, k: json.load(open(f'review/gates_{k}/{f}.json'))
Tx = lambda f, k: Path(f'review/gates_{k}/{f}.txt').read_text(errors='replace').strip()
a, b = J('collapse', 'before'), J('collapse', t)
L.append('COLLAPSE (face-frames; worst single-frame region counts that changed, before -> after)')
for c in a:
    wa, wb = a[c]['worst'], b[c]['worst']
    ch = {k: f'{wa.get(k, 0)}->{wb.get(k, 0)}' for k in sorted(set(wa) | set(wb)) if wa.get(k, 0) != wb.get(k, 0)}
    L.append(f"  {c:14s} {a[c]['face_frames']:5d} -> {b[c]['face_frames']:5d}  {ch}")
L.append(f"  TOTAL face-frames {sum(a[c]['face_frames'] for c in a)} -> {sum(b[c]['face_frames'] for c in b)}")
a, b = J('robe', 'before'), J('robe', t)
L.append('ROBE (boots through the robe: frames / worst edges per side and inner)')
for c in a:
    for s in ('L', 'R', 'inner'):
        x, y = a[c][s], b[c][s]
        if (x['frames'], x['worst']) != (y['frames'], y['worst']):
            L.append(f"  {c:14s} {s:5s} {x['frames']}f/{x['worst']}e -> {y['frames']}f/{y['worst']}e")
L.append('HAIR (frames crossing / worst edges; changed lines)')
for la, lb in zip(Tx('hair', 'before').splitlines(), Tx('hair', t).splitlines()):
    if la != lb:
        L.append(f'  {la}\n    -> {lb}')
a, b = J('arm_hand', 'before')['clips'], J('arm_hand', t)['clips']
L.append('ARM_HAND (per side: changed fields)')
for c in a:
    for s in a[c]:
        x, y = a[c][s], b[c][s]
        ch = {k: f'{x[k]}->{y[k]}' for k in x if not k.endswith('frame48') and x[k] != y[k]}
        if ch:
            L.append(f'  {c:14s} {s} {ch}')
a, b = Tx('jitter', 'before').splitlines()[-1], Tx('jitter', t).splitlines()[-1]
L.append(f'JITTER last line: {a} -> {b}')
for f in ('detached', 'flat', 'winding', 'bone_length', 'same_clips', 'forearm_poke', 'texture_quality'):
    try:
        x, y = Tx(f, 'before'), Tx(f, t)
        if x != y:
            L.append(f'{f.upper()}:\n  before: ' + x.replace('\n', '\n          ')[:1500] + '\n  after:  ' + y.replace('\n', '\n          ')[:1500])
        else:
            L.append(f'{f.upper()}: identical')
    except FileNotFoundError as e:
        L.append(f'{f.upper()}: missing {e.filename}')
try:
    a, b = J('sleeve_gate', 'before'), J('sleeve_gate', t)
    L.append('SLEEVE (changed entries)')
    def flat(d, p=''):
        out = {}
        for k, v in (d.items() if isinstance(d, dict) else enumerate(d)):
            if isinstance(v, (dict, list)):
                out.update(flat(v, f'{p}{k}.'))
            else:
                out[f'{p}{k}'] = v
        return out
    fa, fb = flat(a), flat(b)
    for k in fa:
        if fa[k] != fb.get(k):
            L.append(f'  {k}: {fa[k]} -> {fb.get(k)}')
except FileNotFoundError as e:
    L.append(f'SLEEVE: missing {e.filename}')
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
