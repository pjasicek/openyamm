#!/usr/bin/env python3
"""Faces of the eyes and lips kept exactly (rest-pose positions found from the base colour: the darkest iris/lash
faces and the reddest lip faces of the face group): head-atlas faces within REA_EYE_R (default 0.014 m) of either eye
centre, or inside the mouth ellipsoid (2.2 x 1.6 x 1.1 cm half-axes). Usage: face_keep.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); head = info['u'] > .505
EYES = np.array([[-0.045, -0.045, 1.583], [0.006, -0.040, 1.584]]); MOUTH = np.array([-0.017, -0.050, 1.524])
r = float(os.environ.get('REA_EYE_R', '0.014'))
eye = head & (np.linalg.norm(c[:, None] - EYES[None], axis=2).min(1) < r)
mouth = head & ((((c - MOUTH) / [0.022, 0.016, 0.011]) ** 2).sum(1) < 1)
keep = np.load(sys.argv[1]) | eye | mouth
np.save(sys.argv[2], keep); print('FACE KEEP eyes', int(eye.sum()), 'mouth', int(mouth.sum()), 'total keep', int(keep.sum()))
