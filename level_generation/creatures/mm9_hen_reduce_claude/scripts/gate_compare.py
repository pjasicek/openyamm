#!/usr/bin/env python3
"""Installed vs candidate gate summary (review/gates_before/ vs review/gates_<tag>/) -> review/gates_compare_<tag>.txt:
floor min/max (foot contact), jitter p99, body-in-body pairs, bone ratio per clip (extra_clip_gates), edge-ratio p1/p99/max and
lowest point (gates.py), plus the region/fold, detached, flat, texture, winding and same_clips text. Usage: gate_compare.py <tag>"""
import json, re, sys
from pathlib import Path
tag = sys.argv[1]; A, B = Path('review/gates_before'), Path(f'review/gates_{tag}')
def clip_rows(p):
    out = {}
    for l in p.read_text().splitlines():
        m = re.match(r'(?:new|ref) (\w+) (\{.*\})', l)
        if m and l.startswith('new'): out[m.group(1)] = json.loads(m.group(2))
    return out
def gate_rows(p):
    out = {}
    for l in p.read_text().splitlines():
        m = re.match(r"(\w+) (\{.*\})", l)
        if m: out[m.group(1)] = eval(m.group(2))
    return out
ca, cb = clip_rows(A / 'clip_gates.txt'), clip_rows(B / 'clip_gates.txt'); ga, gb = gate_rows(A / 'gates.txt'), gate_rows(B / 'gates.txt')
L = [f'gates installed -> {tag}', 'clip: floor min/max cm | jitter p99 mm/f2 | body-in-body pairs | bone ratio | edge p1 / p99 / max | lowest m']
for c in ca:
    a, b = ca[c], cb[c]; x, y = ga.get(c, {}), gb.get(c, {})
    L.append(f"{c:12s} {a['floor_min_cm']}/{a['floor_max_cm']} -> {b['floor_min_cm']}/{b['floor_max_cm']} | {a['jitter_p99_mm_f2']} -> {b['jitter_p99_mm_f2']} | "
             f"{a['body_in_body_max_pairs']} -> {b['body_in_body_max_pairs']} | {a['bone_worst_ratio']} -> {b['bone_worst_ratio']} | "
             f"{x.get('edge_ratio_p1')}/{x.get('edge_ratio_p99')}/{x.get('edge_ratio_max')} -> {y.get('edge_ratio_p1')}/{y.get('edge_ratio_p99')}/{y.get('edge_ratio_max')} | "
             f"{x.get('lowest')} -> {y.get('lowest')}")
for f in ('region.txt', 'fold.txt', 'detached.txt', 'flat.txt', 'texture_quality.txt', 'winding.txt', 'same_clips.txt'):
    if (A / f).exists():
        L.append(f'== {f}'); L += ['  before: ' + l for l in (A / f).read_text().strip().splitlines()[-16:]]
        L += ['  ' + tag + ': ' + l for l in (B / f).read_text().strip().splitlines()[-16:]]
Path(f'review/gates_compare_{tag}.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))
