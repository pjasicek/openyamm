#!/usr/bin/env python3
"""Installed vs candidate gate numbers for the sheep (review/gates_before vs review/gates_<tag>): gates.py stretch/lowest/seam,
extra_clip_gates (floor min/max = hoof contact, jitter p99, bone ratio, body-in-body), fold-overs per clip, and the text gates.
Usage: gate_compare_ram.py <tag>"""
import json, re, sys
from pathlib import Path
t = sys.argv[1]; A = Path('review/gates_before'); B = Path(f'review/gates_{t}')
a, b = json.load(open(A / 'gates.json')), json.load(open(B / 'gates.json'))
print('GATES.PY (edge ratio min/max/p1/p99, lowest m, seam):')
for c in a:
    ks = [k for k in a[c] if k in b[c]]
    diff = [k for k in ks if a[c][k] != b[c][k]]
    print(f"  {c:12s} " + ', '.join(f"{k} {a[c][k]} -> {b[c][k]}" for k in diff) if diff else f"  {c:12s} identical")


def clip_lines(p):
    out = {}
    for line in open(p):
        m = re.match(r'(new|ref) (\S+) (\{.*\})', line.strip())
        if m:
            out[m.group(2)] = json.loads(m.group(3))
    return out


a, b = clip_lines(A / 'clip_gates.txt'), clip_lines(B / 'clip_gates.txt')
print('CLIP GATES (floor min/max cm, jitter p99 mm/f2, bone ratio, body-in-body pairs):')
for c in a:
    k = lambda z: (z['floor_min_cm'], z['floor_max_cm'], z['jitter_p99_mm_f2'], z['bone_worst_ratio'], z['body_in_body_max_pairs'])
    print(f"  {c:12s} {k(a[c])} -> {k(b[c])}{'' if k(a[c]) == k(b[c]) else '  *'}")


def fold(p):
    s = open(p).read(); m = re.search(r'OVER \d+ (\{.*\})', s); tot = re.search(r'TOTAL (\d+)', s)
    return eval(m.group(1)), int(tot.group(1))


(fa, ta), (fb, tb) = fold(A / 'fold.txt'), fold(B / 'fold.txt')
print(f'FOLD-OVER face-frames (worst frame, total) per clip; TOTAL {ta} -> {tb}:')
for c in fa:
    print(f"  {c:12s} {fa[c]} -> {fb[c]}{'  +' if fb[c][1] > fa[c][1] else ''}")
for f in ('detached', 'flat', 'winding', 'texture_quality', 'same_clips'):
    print(f.upper()); print('  ' + open(A / f'{f}.txt').read().strip().splitlines()[-1]); print('  ' + open(B / f'{f}.txt').read().strip().splitlines()[-1])
