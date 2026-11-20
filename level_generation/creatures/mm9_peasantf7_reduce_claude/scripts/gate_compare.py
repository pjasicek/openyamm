#!/usr/bin/env python3
"""Per-clip before/after of PeasantF7's gates (review/gates_before vs review/gates_<tag>): collapse, robe (legs through the skirt),
arm/hand, jitter, sleeve poke, see-through, LOD check and the one-line audits; only clips that changed are listed.
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
L.append('ROBE (legs through the skirt: frames / max cm, cords)')
for c in a:
    x, y = a[c], b[c]
    if (x['frames'], x['max_cm'], x['cord_frames']) != (y['frames'], y['max_cm'], y['cord_frames']):
        L.append(f"  {c:14s} {x['frames']}f/{x['max_cm']}cm -> {y['frames']}f/{y['max_cm']}cm (cords {x['cord_frames']} -> {y['cord_frames']})")
L.append('  (no other changes)' if L[-1].startswith('ROBE') else '')
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
for f in ('detached', 'flat', 'winding', 'bone_length', 'same_clips', 'texture_quality'):
    try:
        x, y = Tx(f, 'before'), Tx(f, t)
        if x != y:
            L.append(f'{f.upper()}:\n  before: ' + x.replace('\n', '\n          ')[:1500] + '\n  after:  ' + y.replace('\n', '\n          ')[:1500])
        else:
            L.append(f'{f.upper()}: identical')
    except FileNotFoundError as e:
        L.append(f'{f.upper()}: missing {e.filename}')
L.append('SLEEVE POKE (changed lines)')
for la, lb in zip(Tx('sleeve_poke', 'before').splitlines(), Tx('sleeve_poke', t).splitlines()):
    if la != lb:
        L.append(f'  {la}\n    -> {lb}')
try:
    a, b = J('see_through', 'before'), J('see_through', t)
    L.append('SEE_THROUGH (per clip and zone: hole px max / frames with holes; inside px max), before -> after')
    for c in a['clips']:
        za, zb = a['clips'][c]['zones'], b['clips'][c]['zones']
        for z in sorted(set(za) | set(zb)):
            x, y = za.get(z, {}), zb.get(z, {})
            fx = (x.get('hole_max', 0), len(x.get('hole_frames', [])), x.get('inside_max', 0))
            fy = (y.get('hole_max', 0), len(y.get('hole_frames', [])), y.get('inside_max', 0))
            L.append(f"  {c:10s} {z:9s} {fx[0]}px/{fx[1]}f/in {fx[2]} -> {fy[0]}px/{fy[1]}f/in {fy[2]}" + ('' if fx == fy else '  *'))
except FileNotFoundError as e:
    L.append(f'SEE_THROUGH: missing {e.filename}')
for f in ('uv_escape',):
    try:
        L.append(f.upper() + ':\n  before: ' + '\n          '.join(x for x in Tx(f, 'before').splitlines() if 'Saved' not in x and 'render' not in x and x.strip())[-1500:]
                 + '\n  after:  ' + '\n          '.join(x for x in Tx(f, t).splitlines() if 'Saved' not in x and 'render' not in x and x.strip())[-1500:])
    except FileNotFoundError as e:
        L.append(f'{f.upper()}: missing {e.filename}')
for k in ('before', t):
    try:
        L.append('LOD ' + k + ': ' + ' | '.join(x[:400] for x in Path(f'review/gates_{k}/lod_check.log').read_text().splitlines() if x.startswith('LODCHECK')))
    except FileNotFoundError as e:
        L.append(f'LOD {k}: missing')
open(f'review/gates_compare_{t}.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
