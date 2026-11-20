#!/usr/bin/env python3
"""Posed mesh npz (co, tri, comp) of work/half.glb (rows of a uv npz) at clip@time, for part-coloured back-face renders.
Args: <glb> <uv npz> <out prefix> clip@t [clip@t ...]  -> <prefix>_<clip>_<t>.npz"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
M = Model(Glb(sys.argv[1])); U = np.load(sys.argv[2]); out = sys.argv[3]
ut, um, uo, uc = U['tri'], U['mat'], U['orig'], U['comp']; rows = []; T0 = []; off = 0
for m in range(len(M.primitives)):
    used = np.unique(ut[um == m]); rows.append(used); T0.append(M.primitives[m]['triangles'] + off); off += len(used)
rows = np.concatenate(rows); T0 = np.vstack(T0)
for it in sys.argv[4:]:
    c, t = it.split('@'); P = np.vstack([a for a, _ in M.skinned_positions(M.world(M.sample(c, float(t))))])
    P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]      # glTF -> Blender
    np.savez(f'{out}_{c}_{t}.npz', co=P, tri=T0, comp=uc[rows]); print('POSED', it, len(P))
