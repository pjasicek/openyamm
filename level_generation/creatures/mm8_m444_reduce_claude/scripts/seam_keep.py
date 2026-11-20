#!/usr/bin/env python3
"""Keep faces touching a UV-chart border exactly, in the given region labels (work/groups.npy). The left hand's
texture already bleeds orange gutter lines along its chart borders; collapses across those borders widen them into
streaks (Smuggler, review/close lhand). A vertex is on a border when its wedge UVs differ between its faces.
Usage: seam_keep.py <base keep .npy> <out .npy> <label,...>"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; wuv = d['wuv'].reshape(-1, 3, 2)
g = np.load('work/groups.npy'); keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
uv0 = np.full((len(d['verts']), 2), np.nan); seam = np.zeros(len(d['verts']), bool)
for k in range(3):
    for fi, (vi, uv) in enumerate(zip(f[:, k], wuv[:, k])):
        if np.isnan(uv0[vi, 0]):
            uv0[vi] = uv
        elif np.abs(uv0[vi] - uv).max() > 1e-5:
            seam[vi] = True
sel = np.isin(g, [int(x) for x in sys.argv[3].split(',')]) & seam[f].any(1)
keep |= sel
np.save(sys.argv[2], keep); print('SEAMKEEP', int(sel.sum()), 'border faces; kept', n0, '->', int(keep.sum()))
