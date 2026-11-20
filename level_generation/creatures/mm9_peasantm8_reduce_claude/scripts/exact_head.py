#!/usr/bin/env python3
"""Exact-part check (PeasantM8 reduction; PeasantM7d copy): every installed LOD0 face of the exact head shell (face, ears, neck,
brows, moustache, hairline, collar band: part 3 and keep of work/glb_sets_<set>.npz) and every kept face is present in the candidate with the same corner vertices, and those
vertices carry identical bytes (position, normal, UV, joints, weights). Usage: exact_head.py <candidate.glb> <set>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, A = glbio.load(HERE / 'before' / 'mm9_peasantm8.glb', 'PeasantM8')
_, _, _, B = glbio.load(sys.argv[1], 'PeasantM8')
s = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2]}.npz'); part, keep, mat = s['part'], s['keep'], s['mat']
off = 0
for k, name in enumerate(['PeasantM8', 'PeasantM8Head']):
    a, b = A[name], B[name]; n = len(a['T'])
    key = lambda d: [np.concatenate([d[x][i].ravel() for x in ('P', 'N', 'UV', 'J', 'W')]).tobytes() for i in range(len(d['P']))]
    ka, kb = key(a), key(b)
    same_v = len(set(kb) - set(ka)) == 0      # every candidate vertex record (all attributes) is an installed one
    have = {frozenset(kb[i] for i in t) for t in b['T'].tolist()}
    for label, m in (('exact head shell', (part[off:off + n] == 3) & keep[off:off + n]), ('kept', keep[off:off + n])):
        want = [frozenset(ka[i] for i in t) for t in a['T'][m].tolist()]
        miss = sum(1 for t in want if t not in have)
        print(f'{name}: every candidate vertex an installed one {same_v}; {label} faces {len(want)} missing {miss}')
    off += n
