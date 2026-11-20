#!/usr/bin/env python3
"""Ivory fringe faces kept exactly: the jagged ivory fringes at the calves (z 0.16-0.42), below the arm bands
(|x| > 0.17, z 1.20-1.36) and at the neck (|x| < 0.17, z 1.15-1.45, front collar). They are spikes of the one
welded surface; every collapse rounds their points (the ladder's max error sits there at every step).
Usage: fringe_keep.py <base keep .npy or -> <out .npy>"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
keep = np.zeros(len(f), bool) if sys.argv[1] == '-' else np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
iv = np.load('work/color_class.npy') == 'ivory'; head = np.load('work/set_head.npy')
c = v[f].mean(1); x, z = np.abs(c[:, 0]), c[:, 2]
calf = (z > .16) & (z < .42)
arm = (x > .17) & (z > 1.20) & (z < 1.36)
neck = (x < .17) & (z > 1.15) & (z < 1.45)
for name, m in [('calf', calf), ('arm', arm), ('neck', neck)]:
    print('FRINGE', name, int((iv & ~head & m).sum()))
keep |= iv & ~head & (calf | arm | neck)
np.save(sys.argv[2], keep); print('KEEP', n0, '->', int(keep.sum()))
