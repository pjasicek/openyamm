#!/usr/bin/env python3
"""Markdown per-model table and fix column from table.json (aggregate.py). Usage: table_md.py > table.md"""
import json
from pathlib import Path

rows = json.load(open(Path(__file__).resolve().parent / 'table.json'))
REBUILD_ATLAS = {'mm6_gua', 'mm6_thf', 'mm6_mer1', 'mm6_pfem'}
ATLAS_LADDER = {'mm8_m516', 'mm8_m608'}
KEEP_MARGINAL = {'mm8_m536'}


def fix(r):
    a = r['after']
    stem, streams = r['stem'], r['streams']
    score_fail = not r['score_pass']
    if stem in REBUILD_ATLAS:
        return 'ladder (required)'
    if stem in KEEP_MARGINAL:
        return 'keep (pre-existing, effect body)'
    if score_fail:
        return 'ladder (pre-existing gate miss)'
    if stem in ATLAS_LADDER:
        return 'ladder (atlas far LOD off LOD0 colours)'
    if a['far_own'] is False:
        return 'keep (atlas far LOD passes)'
    if 'texture' in streams:
        return 'ladder, batch (UV correspondence)'
    if stem == 'mm6_ttn':
        return 'keep (passes; hands not in far chain)'
    return 'keep'


def f(v, digits=1):
    return '-' if v is None else (f'{v:.{digits}f}' if isinstance(v, float) else str(v))


print('| Model | Streams | LOD0 tris | LOD2/3 % | LOD1 out/col | LOD2 out/col | LOD3 out/col | hf2/hf3 (before) |'
      ' Far maps | Shadow worst (> 1 u) | Gates S/F/Sh | Fix |')
print('|---|---|---:|---|---|---|---|---|---|---|---|---|')
for r in rows:
    a, b = r['after'], r['before']
    ratios = a['ratios'] or []
    far = 'own ' + '/'.join(str(max(v)) for v in a['far_sizes'].values() if v) if a['far_own'] else 'LOD0 atlas'
    uv = [x for v in a['far_uv'].values() for x in v]
    if a['far_own'] and uv:
        far += f', UV {min(uv):.2f}-{max(uv):.2f}'
    if a['masks']:
        far += ', ' + '/'.join(a['masks'])
    ramp = max(a['ramps'] or [0])
    far += f', {ramp} ramps'
    shadow = f"{a['shadow_worst']} {a['shadow_out1u'] * 100:.1f} %" if a['shadow_out1u'] is not None else '-'
    gates = ''.join('P' if r[k] else '**F**' for k in ('score_pass', 'far_pass', 'shadow_pass'))
    print(f"| `{r['stem']}` | {r['streams']} | {a['tris'][0]:,} | {ratios[2] * 100:.0f}/{ratios[3] * 100:.0f} | "
          f"{f(a.get('l1_out'))}/{f(a.get('l1_col'))} | {f(a.get('l2_out'))}/{f(a.get('l2_col'))} | "
          f"{f(a.get('l3_out'))}/{f(a.get('l3_col'))} | {f(a.get('l2_hf'), 2)}/{f(a.get('l3_hf'), 2)} "
          f"({f(b.get('l2_hf'), 2)}/{f(b.get('l3_hf'), 2)}) | {far} | {shadow} | {gates} | {fix(r)} |")
