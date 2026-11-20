#!/usr/bin/env python3
"""Every installed triangle of the head pieces (head skin with face and neck seam, ears, HOF2's kerchief: parts 10/11/12) and of
every keep face present in the candidate with identical corner positions, UVs and normals (M=1|2).
Usage: M=1 face_exact.py <candidate.glb> <sets tag>"""
import os
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
M_ = os.environ['M']
_, _, _, S = glbio.load(HERE / 'before' / f'mm9_peasanthof{M_}.glb', 'PeasantHOF'); _, _, _, C = glbio.load(sys.argv[1], 'PeasantHOF')
sets = np.load(HERE / 'work' / f'hof{M_}' / f'glb_sets_{sys.argv[2]}.npz'); part = sets['part']; keep = sets['keep']
body = 'PeasantHOF_A' if M_ == '1' else 'PeasantHOF_C'
off = 0


def rows(d, T):
    return [tuple(np.sort(np.c_[d['P'][t], d['UV'][t], d['N'][t]].round(6), axis=0).ravel()) for t in T]


for name in (body, 'PeasantHOFHead'):
    s, c = S[name], C[name]; n = len(s['T']); sl = slice(off, off + n); off += n
    cs = set(rows(c, c['T']))
    for lab, m in (('head skin+ears+kerchief', np.isin(part[sl], (10, 11, 12))), ('all kept', keep[sl])):
        if not m.any():
            continue
        miss = sum(r not in cs for r in rows(s, s['T'][m]))
        print(f'FACEEXACT {name} {lab}: {int(m.sum())} installed faces, missing in candidate {miss}')
