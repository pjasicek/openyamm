#!/usr/bin/env python3
"""Every finger kept: per finger joint of both hands, the number of head-set vertices it dominates and the farthest of them
from the hand joint (the fingertip reach, from the installed hand vertices' centre) in the installed file and a candidate. Usage: finger_check.py <candidate glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
rows = {}; BASE = {}
for k, f in (('inst', HERE / 'before' / 'mm9_annud.glb'), ('cand', Path(sys.argv[1]))):
    doc, _, nd, D = glbio.load(f, 'Annud'); jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
    d = D['AnnudHead']; used = np.unique(d['T']); P = d['P'][used]; J = d['J'][used]; W = d['W'][used]
    dom = np.array([jn[J[i][W[i].argmax()]] for i in range(len(J))])
    for side in ('L', 'R'):
        hand = dom == f'Bip01 {side} Hand'
        base = BASE.setdefault(side, P[hand].mean(0))     # the installed hand centre for both files
        for name in sorted({x for x in dom if x.startswith(f'Bip01 {side} ') and any(s in x for s in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))}):
            m = dom == name
            rows.setdefault(name, {})[k] = (int(m.sum()), float(np.linalg.norm(P[m] - base, axis=1).max() * 1000) if m.any() else 0)
bad = 0
for name, r in rows.items():
    a, b = r.get('inst', (0, 0)), r.get('cand', (0, 0)); flag = '' if b[0] > 0 and b[1] >= a[1] - 1.0 else '  <-- CHECK'
    bad += bool(flag); print(f'{name:22s} verts {a[0]:4d} -> {b[0]:4d}   reach mm {a[1]:6.1f} -> {b[1]:6.1f}{flag}')
print('FINGERS', len(rows), 'joints, flagged', bad)
