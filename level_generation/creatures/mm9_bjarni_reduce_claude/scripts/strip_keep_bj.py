#!/usr/bin/env python3
"""Bjarni trouser side strips (painted black/red band with white studs down each outer leg, and the knee-patch stitching):
a60 smeared a black wedge beside the R strip (review/crop_h1_strip_a60.png). Every trouser face (set part 1) whose UV
triangle samples (7 per face, tex_Bjarni_A) touch the band (value < DARK) or a stud (min channel > WHITE), plus RING rings
of neighbours -> work/strip_keep.npy (bool per GLB face, both primitives). Usage: strip_keep_bj.py [set tag, default a]"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
DARK = float(E('DARK', '0.16')); WHITE = float(E('WHITE', '0.70')); RING = int(E('RING', '1'))
tag = sys.argv[1] if len(sys.argv) > 1 else 'a'
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); part = s['part']
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_bjarni.glb', 'Bjarni')
d = D['Bjarni']; P, T, U = d['P'], d['T'], d['UV']; nb = len(T)
img = np.asarray(Image.open(HERE / 'work' / 'tex_Bjarni_A.png').convert('RGB'), np.float64) / 255; S = img.shape[0]
bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
px = np.clip((np.einsum('sk,fkc->fsc', bary, U[T]) * S).astype(int), 0, S - 1)
col = img[px[..., 1], px[..., 0]]                    # (f, 7, 3)
mx = col.max(2); mn = col.min(2)
V = P[T]; C = V.mean(1); fn = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
Y0, Y1 = float(E('Y0', '0.42')), float(E('Y1', '1.0'))
outer = (np.abs(fn[:, 0]) > float(E('NX', '0.35'))) & (np.sign(fn[:, 0]) == np.sign(C[:, 0])) & (C[:, 1] > Y0) & (C[:, 1] < Y1)
band = ((mx < DARK).sum(1) >= int(E('NDARK', '2'))) | ((mn > WHITE).any(1))
hit = (part[:nb] == 1) & band & outer
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
m = hit.copy()
for _ in range(RING):
    v = np.zeros(w.max() + 1, bool); v[FT[m].ravel()] = True
    m |= (part[:nb] == 1) & v[FT].any(1)
out = np.zeros(len(part), bool); out[:nb] = m
np.save(HERE / 'work' / 'strip_keep.npy', out)
print('outer thigh faces', int(((part[:nb] == 1) & outer).sum()), 'trouser faces', int((part[:nb] == 1).sum()), 'strip/stud hits', int(hit.sum()), f'with {RING} ring', int(m.sum()))
from set_view import views  # noqa: E402
rgb = np.tile([[150, 120, 80]], (nb, 1)); rgb[m] = (220, 40, 40); rgb[hit] = (250, 230, 40)
sel = part[:nb] == 1
views(P, T[sel], rgb[sel], (-0.4, 0.4, 0.0, 1.1), HERE / 'review' / 'strip_keep.png', size=480)
