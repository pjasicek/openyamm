#!/usr/bin/env python3
"""See-through rises -> probe jobs: every (clip, zone) whose hole maximum rose by >= MIN px from <before tag> to <cand tag>
(review/gates_<tag>/st_main.json), the candidate's worst (frame, view) and the installed's, each probed on both GLBs by
scripts/st_probe.py (faces hit by the hole pixels). Prints one shell line per probe (run under work/blender.lock).
Usage: probe_queue.py <before glb> <cand glb> <cand tag> [MIN=5] [TOP=18]"""
import json, sys
bglb, cglb, tag = sys.argv[1:4]; MIN = int(sys.argv[4]) if len(sys.argv) > 4 else 5; TOP = int(sys.argv[5]) if len(sys.argv) > 5 else 18
B = json.load(open('review/gates_before/st_main.json'))['clips']; C = json.load(open(f'review/gates_{tag}/st_main.json'))['clips']
rises = []
for c in C:
    for z, v in C[c]['zones'].items():
        b = B[c]['zones'].get(z, {'hole_max': 0, 'worst': None})
        if z != 'none' and v['hole_max'] - b['hole_max'] >= MIN:
            rises.append((v['hole_max'] - b['hole_max'], c, z, v['worst'], b.get('worst')))
rises.sort(reverse=True)
seen = set()
for d, c, z, wc, wb in rises[:TOP]:
    for w in (wc, wb):
        if not w or (c, w[0], w[1]) in seen:
            continue
        seen.add((c, w[0], w[1]))
        for lab, g in (('before', bglb), (tag, cglb)):
            print(f'probe {lab} {g} {c} {w[0]} {w[1]}  # {z} +{d}')
