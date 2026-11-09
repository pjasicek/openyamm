#!/usr/bin/env python3
"""Delete faces hidden inside other cloth (faces removed only: every kept face keeps its UVs, so the paid paints stay valid): the
underskirt above z -0.30 (MM9 frame) lies inside the gown, whose open hem is at -0.40 (10 cm overlap kept for the fall).
Args: <mesh npz in> <mesh npz out>"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); tri, co, comp = D['tri'], D['co'], D['comp']; names = [str(x) for x in D['names']]
drop = (comp[tri[:, 0]] == names.index('skirt')) & (co[tri][:, :, 2].min(1) > -0.30)
for k in ('tri', 'mat', 'inner'):
    if k in D and len(D[k]) == len(tri): D[k] = D[k][~drop]
np.savez(sys.argv[2], **D); print('TRIM underskirt faces', int(drop.sum()), '->', len(D['tri']))
