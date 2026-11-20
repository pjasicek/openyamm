#!/usr/bin/env python3
"""Keep set of the m628 ladder: bow material (limbs, grip, spare and nocked arrows), string tubes, finger- and
hand-weighted faces (fitted bow grip, 19 capped rigid segments of the bare hand, glove digits), small separate
pieces (work/keep_small.npy) and faces within 1.2 cm of the two coincident body vertex pairs.
Usage: m628_keep.py <out .npy> [extra .npy ...]"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); s = np.load('work/sets.npz'); v, f = d['verts'], d['faces']
dom = s['dom'].astype(str)
parts = {
    'bow': s['mat'] == 1,
    'string': np.char.startswith(dom, 'String'),
    'fingers': np.char.find(dom, 'Finger') >= 0,
    'hands': np.isin(dom, ['B_L_Hand', 'B_R_Hand']),
    'small': np.load('work/keep_small.npy'),
}
body_pairs = [i for i in s['pairs'] if abs(v[i]).max() > .01 and not (abs(v[i, 2] - 1) < .01 and abs(v[i, :2]).max() < .01)]
near = np.zeros(len(v), bool)
for i in body_pairs:
    near |= np.linalg.norm(v - v[i], axis=1) < .012
parts['coincident'] = near[f].any(1)
keep = np.zeros(len(f), bool)
for k, m in parts.items():
    print(f'{k:11s} {int(m.sum()):5d} faces, new {int((m & ~keep).sum())}'); keep |= m
for extra in sys.argv[2:]:
    e = np.load(extra); print('extra', extra, int((e & ~keep).sum())); keep |= e
np.save(sys.argv[1], keep); print('KEEP', int(keep.sum()), 'of', len(f), '; free', int((~keep).sum()),
                                  '; head/jaw free', int((~keep & (d['protect'] > .5)).sum()))
