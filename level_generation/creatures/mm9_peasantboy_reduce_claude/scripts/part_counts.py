#!/usr/bin/env python3
"""Faces per part (make_sets_boy.py parts; linings separate) of a pose-aware step work/<mp>.npz against the installed LOD0.
A face's part = the part of its first vertex (vertices never change part). Usage: part_counts.py <mp npz> [sets tag]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantboy.glb', 'PeasantBoy')
s = np.load(HERE / 'work' / f"glb_sets_{sys.argv[2] if len(sys.argv) > 2 else 'a'}.npz"); tw = np.load(HERE / 'work' / 'twins.npz')
mp = np.load(HERE / 'work' / sys.argv[1]) if sys.argv[1].endswith('.npz') else None
NAMES = ['cloth', 'legs', 'small', 'head', 'hair', 'hands', 'tube', 'linings']
off = 0; tot_b = np.zeros(8, int); tot_a = np.zeros(8, int)
for name in ('PeasantBoy_A', 'PeasantBoyHead'):
    T = D[name]['T']; n = len(T); part = s['part'][off:off + n].copy(); part[tw['lining'][off:off + n].astype(bool)] = 7; off += n
    vp = -np.ones(len(D[name]['P']), int); vp[T.ravel()] = np.repeat(part, 3)
    for f, t in enumerate(T):
        if part[f] == 7:
            vp[t] = 7
    tot_b += np.bincount(part, minlength=8)
    if mp is not None:
        tot_a += np.bincount(vp[mp[name][:, 0]], minlength=8)
print(' | '.join(f'{k} {a:,} -> {c:,}' for k, a, c in zip(NAMES, tot_b, tot_a)), '| total', f'{tot_b.sum():,} -> {tot_a.sum():,}')
