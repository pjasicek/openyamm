#!/usr/bin/env python3
"""Skraelos copy: every installed triangle of the skull (head part 4), of the held props (staff, held skull, pendant) and of every keep face present in the
candidate with identical corner positions, UVs and normals. Usage: face_exact.py <candidate.glb> [sets tag]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_skraelos.glb', 'Skraelos'); _, _, _, C = glbio.load(sys.argv[1], 'Skraelos')
sets = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2] if len(sys.argv) > 2 else "a"}.npz'); part = sets['part']; keep = sets['keep']
off = 0
for name in ('Skraelos', 'SkraelosHead'):
    s, c = S[name], C[name]; n = len(s['T']); sl = slice(off, off + n); off += n
    key = lambda d, T: {tuple(np.round(np.concatenate([d['P'][T[k]] for k in range(3)] + [d['UV'][T[k]] for k in range(3)] + [d['N'][T[k]] for k in range(3)]), 6)) for _ in [0]} if False else None
    def rows(d, T):
        return [tuple(np.round(np.r_[np.sort(np.c_[d['P'][t], d['UV'][t], d['N'][t]].round(6), axis=0).ravel()], 6)) for t in T]
    cs = set(rows(c, c['T']))
    for lab, m in (('skull (cranium, jaw, teeth, ember eyes)', part[sl] == 4), ('held props (staff, held skull, pendant)', np.isin(part[sl], (7, 8, 9))), ('all kept', keep[sl])):
        if not m.any():
            continue
        miss = sum(r not in cs for r in rows(s, s['T'][m]))
        print(f'{name} {lab}: {int(m.sum())} installed faces, missing in candidate {miss}')
