#!/usr/bin/env python3
"""Body shells (fit_yan.py) + placed head-only model (face_npz.py) in one npz for the voxel wrap: Meshy's own head on the body
shrinks into the new head first (as union_bf.py), so the wrap's union of volumes keeps only the new head. Parts: 0 body, 10 face,
13 eyes (left out of the wrap, added back by body_close.py). Args: <shells npz> <face npz> <out npz>"""
import sys
import numpy as np
A = np.load(sys.argv[1]); B = np.load(sys.argv[2])
C = np.array([0.0, -0.03, 1.10]); SHR = 0.55


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


co = A['co'].copy()
t = sstep(co[:, 2], 0.93, 1.00) * (1 - sstep(np.abs(co[:, 0]), 0.13, 0.20))
# Meshy's own beard hangs lower, in front of the throat: it goes too
t = np.maximum(t, sstep(co[:, 2], 0.80, 0.86) * (1 - sstep(co[:, 1], -0.10, -0.06)) * (1 - sstep(np.abs(co[:, 0]), 0.08, 0.12)))
co += t[:, None] * (SHR - 1) * (co - C)
print('SHRUNK', int((t > 0).sum()))
np.savez(sys.argv[3], co=np.vstack([co, B['co']]), tri=np.vstack([A['tri'], B['tri'] + len(co)]),
         part=np.concatenate([A['part'], B['part']]))
print('COMBINED', len(co) + len(B['co']))
