#!/usr/bin/env python3
"""Sheep body = the Ram's body byte for byte (positions, UVs, joints, weights, indices of Sheep_A == Ram_A), so the family cut is
the Ram's: work/mp_ram_b_r55.npz {Sheep_A: the Ram's b r55 Ram_A triangles} (../mm9_ram_reduce_claude/work/mp_b_r55.npz). Checks
the byte identity first. Usage: from_ram_cut.py"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
RAM = HERE.parent / 'mm9_ram_reduce_claude'
d1, b1 = gb.read(RAM / 'before' / 'mm9_ram.glb'); d2, b2 = gb.read(HERE / 'before' / 'mm9_sheep.glb')
p1 = gb.prims(d1, b1, next(n for n in d1['nodes'] if n.get('name') == 'Ram')['mesh'])[0]
p2 = gb.prims(d2, b2, next(n for n in d2['nodes'] if n.get('name') == 'Sheep')['mesh'])[0]
for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0', 'T'):
    if k in p1:
        assert np.array_equal(p1[k], p2[k]), k
        print('IDENTICAL', k, p1[k].shape)
T = np.load(RAM / 'work' / 'mp_b_r55.npz')['Ram_A']
np.savez(HERE / 'work' / 'mp_ram_b_r55.npz', Sheep_A=T)
print('CUT Sheep_A', len(p2['T']), '->', len(T))
