#!/usr/bin/env python3
"""Head-set classes for the prio-1 keep set (non-human head: the 'face' is eyes, mouth, teeth, tongue, horn roots).
Classes per LesserDemonHead face: 1 face (kept exactly), 2 cranium/back of head (cut), 3 horn shaft (cut gently, tips
locked), 4 horn root ring (kept), 5 small pieces (teeth, eyes, tongue: kept). Writes work/head_cls.npy + review/head_classes.png.
Env: FACE_Z (front of this z is face), HORN_X (|x| beyond is horn), ROOT_W (root band width)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
from class_render import render
FACE_Z = float(os.environ.get('FACE_Z', '0.66')); HORN_X = float(os.environ.get('HORN_X', '0.15')); ROOT_W = float(os.environ.get('ROOT_W', '0.03'))
MOUTH = float(os.environ.get('MOUTH', '0.03'))
doc, b = bglbio.read(HERE / 'before' / 'mm9_lesserdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh'])[1]; P = pr['POSITION'].astype(np.float64); T = pr['T']
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'][g['mat'] == 1]
C = P[T].mean(1)
cls = np.full(len(T), 2)
shell = part == 10
cls[~shell] = 5
cls[shell & (C[:, 2] > FACE_Z)] = 1
# mouth cavity and lips: shell faces near teeth/tongue/eyes
small = np.vstack([P[T[~shell]].reshape(-1, 3)])
dd, _ = cKDTree(small).query(C); cls[shell & (dd < MOUTH)] = 1
horn = shell & (np.abs(C[:, 0]) > HORN_X) & (C[:, 1] > 1.9)
cls[horn] = 3
root = shell & (np.abs(np.abs(C[:, 0]) - HORN_X) < ROOT_W) & (C[:, 1] > 1.9) & ~(cls == 1)
cls[horn & (np.abs(C[:, 0]) < HORN_X + ROOT_W)] = 4
np.save(HERE / 'work' / 'head_cls.npy', cls)
print('HEAD CLASSES', {int(k): int((cls == k).sum()) for k in np.unique(cls)})
render(P, T, cls, ['front', 'side', 'back', 'top', 'q34', 'below'], HERE / 'review' / 'head_classes.png', size=500)
