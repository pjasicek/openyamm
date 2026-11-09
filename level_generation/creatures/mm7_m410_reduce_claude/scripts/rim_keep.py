#!/usr/bin/env python3
"""Cap brim and collar top (m410): knitted-cap faces whose vertices all lie within REA_RIM_H (default 0.025 m) of the
cap's lowest point in their 15-degree azimuth sector about the cap axis (at 70 % the brim folded in under the face),
and torso-shell faces with a vertex above REA_COLLAR_Z (default 1.47 m: the high collar's top edge went jagged at the
back of the neck). Usage: rim_keep.py <out .npy>"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; p = np.load('work/pieces.npy')
hv = np.unique(f[p == 3]); axis = v[hv, :2].mean(0)
az = np.arctan2(*(v[:, :2] - axis).T[::-1]); sector = ((az + np.pi) / (2 * np.pi) * 24).astype(int) % 24
low = np.full(24, 9.0); np.minimum.at(low, sector[hv], v[hv, 2])
near = v[:, 2] < low[sector] + float(os.environ.get('REA_RIM_H', '0.025'))
rim = (p == 3) & near[f].all(1)
collar = (p == 1) & (v[f][:, :, 2].max(1) > float(os.environ.get('REA_COLLAR_Z', '1.47')))
np.save(sys.argv[1], rim | collar); print('RIM cap brim', int(rim.sum()), 'collar top', int(collar.sum()))
