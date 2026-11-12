#!/usr/bin/env python3
"""Seam-trial faces npz (pos per vertex, tri, uv per corner v-up) -> layout npz (pos, uv per corner glTF v-down).

    faces2layout.py <faces.npz> <out layout.npz>
"""
import sys

import numpy as np

d = np.load(sys.argv[1])
uv = d['uv'].astype(np.float64).copy()
uv[..., 1] = 1.0 - uv[..., 1]
np.savez(sys.argv[2], pos=d['pos'][d['tri']], uv=uv, margin=2)
