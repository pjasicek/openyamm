#!/usr/bin/env python3
"""Hair reshape without touching the paid UV layout: a new geometry npz from make_f6_geom.py with the SAME topology (same hairline,
press box, ears, braid; only the hair thickness options differ) replaces the positions of work/asm_f6.npz (faces kept: the 84 dropped fins
stay dropped) and of every split vertex of work/uv.npz (co = asm co[orig]). Args: <new geom npz>   (project folder; writes asm_f6.npz, uv.npz)"""
import sys
import numpy as np
N = np.load(sys.argv[1]); A = dict(np.load('work/asm_f6.npz')); U = dict(np.load('work/uv.npz'))
assert N['co'].shape == A['co'].shape and (N['comp'] == A['comp']).all(), (N['co'].shape, A['co'].shape)
d = np.linalg.norm(N['co'] - A['co'], axis=1); names = [str(x) for x in A['names']]
print('SWAP moved', {n: round(float(d[A['comp'] == i].max()) * 1000, 1) for i, n in enumerate(names) if d[A['comp'] == i].max() > 1e-7})
A['co'] = N['co']; U['co'] = N['co'][U['orig']]
np.savez('work/asm_f6.npz', **A); np.savez('work/uv.npz', **U); print('SWAP done')
