#!/usr/bin/env python3
"""Faces of work/mesh_in.npz with a vertex that a helper bone (*_h half joints, Skirt_* hinges; HELPERS regex) weights
at least WMIN, per helper. Reads the weights from work/source.blend's dump (work/src_weights.npz, dump_weights.py).
Usage: helper_faces.py <out .npy> [regex]"""
import os, re, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
W = np.load(HERE / 'work' / 'src_weights.npz'); names = [str(n) for n in W['names']]; w = W['weights']
d = np.load(HERE / 'work' / 'mesh_in.npz'); F = d['faces']
rx = re.compile(sys.argv[2] if len(sys.argv) > 2 else r'_h$'); WMIN = float(os.environ.get('WMIN', '0.5'))
part = np.load(HERE / 'work' / 'face_part.npy')
out = np.zeros(len(F), bool)
for k, n in enumerate(names):
    if rx.search(n):
        hv = w[:, k] >= WMIN; f = hv[F].any(1); out |= f
        print(f'{n:22s} verts {int(hv.sum()):4d} faces {int(f.sum()):4d} parts {dict(zip(*np.unique(part[f], return_counts=True)))}')
print('TOTAL faces', int(out.sum()))
np.save(sys.argv[1], out)
