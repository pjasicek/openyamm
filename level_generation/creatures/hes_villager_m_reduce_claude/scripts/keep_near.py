#!/usr/bin/env python3
"""Keep the faces of the large pieces within R metres (rest pose) of the kept small pieces too (hvm: the decimated coat
rose over the chest pin's disc and the clasps at 72 %). Usage: keep_near.py <keep in> <small .npy> <out> [R]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
kin, ksmall, out = sys.argv[1:4]; R = float(sys.argv[4]) if len(sys.argv) > 4 else 0.015
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; keep = np.load(kin).copy(); small = np.load(ksmall)
pts = v[np.unique(f[small])]; t = cKDTree(pts)
near = np.array([t.query(p)[0] < R for p in v])
n0 = int(keep.sum()); keep |= near[f].any(1)
np.save(out, keep); print('KEEPNEAR', n0, '->', int(keep.sum()))
