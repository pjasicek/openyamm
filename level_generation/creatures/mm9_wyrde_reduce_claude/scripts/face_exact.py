#!/usr/bin/env python3
"""Every installed triangle of the kept sets (the kept head faces: face skin, neck, lips, circlet, eyes, hair/hood edge; and every keep face) present in the
candidate with identical corner positions, UVs and normals. Usage: face_exact.py <candidate.glb> [sets tag]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_wyrde.glb', 'Wyrde'); _, _, _, C = glbio.load(sys.argv[1], 'Wyrde')
sets = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2] if len(sys.argv) > 2 else "a"}.npz'); part = sets['part']; keep = sets['keep']
off = 0
for name in ('Wyrde_YOUNG', 'WyrdeHead'):
    s, c = S[name], C[name]; n = len(s['T']); sl = slice(off, off + n); off += n
    key = lambda d, T: {tuple(np.round(np.concatenate([d['P'][T[k]] for k in range(3)] + [d['UV'][T[k]] for k in range(3)] + [d['N'][T[k]] for k in range(3)]), 6)) for _ in [0]} if False else None
    def rows(d, T):
        return [tuple(np.round(np.r_[np.sort(np.c_[d['P'][t], d['UV'][t], d['N'][t]].round(6), axis=0).ravel()], 6)) for t in T]
    cs = set(rows(c, c['T']))
    for lab, m in (('face set (kept head faces)', keep[sl] & (part[sl] == 0)), ('all kept', keep[sl])):
        if not m.any():
            continue
        miss = sum(r not in cs for r in rows(s, s['T'][m]))
        print(f'{name} {lab}: {int(m.sum())} installed faces, missing in candidate {miss}')
