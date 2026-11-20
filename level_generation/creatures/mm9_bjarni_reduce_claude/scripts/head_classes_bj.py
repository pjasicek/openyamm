#!/usr/bin/env python3
"""Bjarni head shell survey (read-only): Bjarni's face, beard and hair are one Meshy shell (2,055 faces, head prim). Per face the
mean colour of 7 samples in its UV triangle -> skin (warm, light) or hair (brown/grey, darker), and a scalp region by position:
hair-class faces above the brows or behind the ears (the cuttable hair mass); the beard, moustache, brows and everything
in front of the ears stay with the face. Writes work/head_classes_bj.npz (cls 0 skin / 1 hair-coloured, scalp mask, comp) and
review/head_classes_bj.png (red skin, brown hair-coloured, yellow = scalp: the cuttable part)."""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from set_view import views  # noqa: E402
E = lambda k, d: float(os.environ.get(k, d))
BROW_Y = E('BROW_Y', '1.700'); EAR_Z = E('EAR_Z', '-0.035')
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_bjarni.glb', 'Bjarni')
d = D['BjarniHead']; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]
img = np.asarray(Image.open(HERE / 'work' / 'tex_BjarniHead_A.png').convert('RGB'), np.float64) / 255
S = img.shape[0]
bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
px = np.clip((np.einsum('sk,fkc->fsc', bary, U[T]) * S).astype(int), 0, S - 1)
col = img[px[..., 1], px[..., 0]].mean(1)
mx, mn = col.max(1), col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
r, g, b = col.T
cls = np.zeros(len(T), int)
# skin: light and red-dominant (r - g large); hair/beard: darker brown or grey
skin = (mx > E('SKIN_V', '0.50')) & ((r - g) > E('SKIN_RG', '0.10'))
cls[~skin] = 1
main = np.bincount(fl).argmax(); C = P[T].mean(1)
shell = fl == main
scalp = shell & (cls == 1) & ((C[:, 1] > BROW_Y) | (C[:, 2] < EAR_Z))
print('shell', int(shell.sum()), 'skin', int((shell & (cls == 0)).sum()), 'hair-coloured', int((shell & (cls == 1)).sum()),
      'scalp (cuttable)', int(scalp.sum()), 'face y', C[shell, 1].min().round(3), C[shell, 1].max().round(3))
np.savez(HERE / 'work' / 'head_classes_bj.npz', cls=cls, scalp=scalp, comp=fl, main=main)
rgb = np.where(cls[:, None] == 0, [[220, 60, 60]], [[120, 80, 50]]); rgb[scalp] = (230, 210, 40)
m = shell
views(P, T[m], rgb[m], (-0.2, 0.2, 1.45, 1.82), HERE / 'review' / 'head_classes_bj.png', size=420)
