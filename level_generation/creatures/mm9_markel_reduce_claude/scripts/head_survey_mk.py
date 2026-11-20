#!/usr/bin/env python3
"""PeasantM5 head primitive survey (read-only): per face the mean tier-A texture colour and the component; flat views of the
head (all comps, then each of face shell / hair shell / neck piece alone) -> review/head_survey.png, plus open-edge counts."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from set_view import view  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_markel.glb', 'Markel')
d = D['MarkelHead']; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]
img = np.asarray(Image.open(HERE / 'work' / 'tex_MarkelHead_A.png').convert('RGB'), np.float64)
S = img.shape[0]
bary = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4]], float); bary /= bary.sum(1, keepdims=True)
px = np.clip((np.einsum('sk,fkc->fsc', bary, U[T]) * S).astype(int), 0, S - 1)
col = img[S - 1 - px[..., 1], px[..., 0]].mean(1) if False else img[px[..., 1], px[..., 0]].mean(1)
E = np.sort(np.r_[FT[:, [0, 1]], FT[:, [1, 2]], FT[:, [2, 0]]], 1)
ek, ec = np.unique(E, axis=0, return_counts=True)
for c in np.unique(fl):
    m = fl == c
    es = np.sort(np.r_[FT[m][:, [0, 1]], FT[m][:, [1, 2]], FT[m][:, [2, 0]]], 1); k, cc = np.unique(es, axis=0, return_counts=True)
    print('comp', c, int(m.sum()), 'open edges', int((cc == 1).sum()), 'mean colour', col[m].mean(0).round(0))
rgb = col.astype(int)
ims = []
reg = (-0.13, 0.13, 1.42, 1.80)
for sel in [np.abs(P[T].mean(1)[:, 0]) < 0.3, fl == np.bincount(fl).argsort()[-1], fl == np.bincount(fl).argsort()[-2],
            np.isin(fl, [c for c in np.unique(fl) if 250 < (fl == c).sum() < 400])]:
    for ax in ('front', 'right', 'back'):
        ims.append(view(P, T[sel], rgb[sel], ax, reg, 300))
Wd = sum(i.width for i in ims[:3]); H = max(i.height for i in ims)
sheet = Image.new('RGB', (Wd, H * 4), (0, 0, 0))
for k, im in enumerate(ims):
    sheet.paste(im, (sum(i.width for i in ims[(k // 3) * 3:k]), (k // 3) * H))
sheet.save(HERE / 'review' / 'head_survey.png'); print('saved')
