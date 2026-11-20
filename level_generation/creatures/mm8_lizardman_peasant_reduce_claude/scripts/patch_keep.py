#!/usr/bin/env python3
"""Keep faces within REA_PATCH_R (default 0.04 m) of rest-pose points and their X mirrors exactly (a single failing
point every step: the playbook's Titan armpit). Usage: patch_keep.py <base keep .npy or -> <out .npy> x,y,z [x,y,z ...]"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
keep = np.zeros(len(f), bool) if sys.argv[1] == '-' else np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
R = float(os.environ.get('REA_PATCH_R', '0.04'))
for s in sys.argv[3:]:
    p = np.array([float(x) for x in s.split(',')])
    for q in (p, p * [-1, 1, 1]):
        keep |= (np.linalg.norm(v - q, axis=1) < R)[f].any(1)
np.save(sys.argv[2], keep); print('PATCH kept faces', n0, '->', int(keep.sum()))
