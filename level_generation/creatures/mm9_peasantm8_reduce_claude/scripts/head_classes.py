#!/usr/bin/env python3
"""PeasantM8 copy (hue-based hair class). Survey of the head primitive's main component: per face, texture class by the mean colour of 7 samples in its UV triangle
(hair: light, low saturation; tunic: dark; skin: the rest) and position (front of the face: z > FRONT_Z). Read-only; prints counts
and writes work/head_classes.npz (cls per head-prim face: 0 skin, 1 hair, 2 tunic; comp per face)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm8.glb', 'PeasantM8')
d = D['PeasantM8Head']; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]
img = np.asarray(Image.open(HERE / 'work' / 'tex_PeasantM8Head_A.png').convert('RGB'), np.float64) / 255
S = img.shape[0]
bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
uv = np.einsum('sk,fkc->fsc', bary, U[T])
px = np.clip((uv * S).astype(int), 0, S - 1)
col = img[px[..., 1], px[..., 0]].mean(1)
mx, mn = col.max(1), col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
cls = np.zeros(len(T), int)
# PeasantM8: blond golden hair (hue 35-65 deg, saturated) vs pink skin (hue < 30 deg); dark brown = tunic collar band
r_, g_, b_ = col[:, 0], col[:, 1], col[:, 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g_ - b_), 2 * r_ - g_ - b_)) % 360
cls[(hue > float(__import__('os').environ.get('HUE_MIN', '33'))) & (hue < 70) & (sat > 0.35) & (mx >= 0.35)] = 1
cls[(mx < 0.35)] = 2
main = np.bincount(fl).argmax()
cen = P[T].mean(1)
for c in np.unique(fl):
    m = fl == c
    print('comp', c, m.sum(), 'skin', int((m & (cls == 0)).sum()), 'hair', int((m & (cls == 1)).sum()), 'tunic', int((m & (cls == 2)).sum()),
          'y', cen[m, 1].min().round(3), cen[m, 1].max().round(3))
m = fl == main
for zc in (0.0, 0.02, 0.04):
    fr = m & (cen[:, 2] > zc)
    print('main z >', zc, 'faces', fr.sum(), 'hair there', int((fr & (cls == 1)).sum()))
np.savez(HERE / 'work' / 'head_classes.npz', cls=cls, comp=fl, main=main)
