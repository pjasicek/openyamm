#!/usr/bin/env python3
"""Add the tabard back's cloth faces (textile_frac > 0.3, body region, behind y = -0.05, above 0.9 m) plus one ring of
neighbouring faces to a keep set: at the body ratio the leaf heraldry on the back smeared and the white/green split
shifted, while the drift check (colour at nearest points) stayed under its threshold.
Usage: back_textile_keep.py <base keep .npy> <out .npy>"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
t = np.load('work/textile_frac.npy'); reg = np.load('work/regions.npy')
s = (t > .3) & (reg == 1) & (c[:, 1] > -0.05) & (c[:, 2] > 0.9)
vm = np.zeros(len(v), bool); vm[f[s].ravel()] = True
s |= (reg == 1) & vm[f].any(1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= s
np.save(sys.argv[2], keep); print('BACK cloth keep', n0, '->', int(keep.sum()))
