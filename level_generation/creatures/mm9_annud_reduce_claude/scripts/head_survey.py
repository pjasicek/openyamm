#!/usr/bin/env python3
"""Annud head-prim survey (reduction, read-only): the head shell (largest head component: face, ears, scalp, neck, painted
beard) faces under the hair shell (ray from the face centroid along its normal hits a hair-shell face within REACH m) vs open
skin; writes work/head_survey.npz (per AnnudHead face: comp, under_hair, uvcol) and review/head_survey.png
(red open shell, blue under hair, orange hair shell, green hands)."""
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
REACH = float(os.environ.get('REACH', '0.05'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_annud.glb', 'Annud')
d = D['AnnudHead']; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
comps = np.argsort(-cnt)
V = P[T]; C = V.mean(1); Nf = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); Nf /= np.maximum(np.linalg.norm(Nf, axis=1, keepdims=True), 1e-12)
shell = fl == comps[0]; hair = fl == comps[1]
H = V[hair]
def hits(o, dvec):
    e1 = H[:, 1] - H[:, 0]; e2 = H[:, 2] - H[:, 0]
    out = np.zeros(len(o), bool); dist = np.full(len(o), np.inf)
    for i in range(len(o)):
        p = np.cross(dvec[i], e2); det = (e1 * p).sum(1); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0); s = o[i] - H[:, 0]
        u = (s * p).sum(1) * inv; q = np.cross(s, e1); v = (dvec[i] * q).sum(1) * inv; t = (e2 * q).sum(1) * inv
        m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < REACH)
        if m.any():
            out[i] = True; dist[i] = t[m].min()
    return out, dist
under = np.zeros(len(T), bool); ud = np.full(len(T), np.inf)
idx = np.where(shell)[0]; h, dd = hits(C[idx] + Nf[idx] * 1e-4, Nf[idx]); under[idx] = h; ud[idx] = dd
img = np.asarray(Image.open(HERE / 'work' / 'tex_AnnudHead_A.png').convert('RGB')) if (HERE / 'work' / 'tex_AnnudHead_A.png').exists() else None
uvc = U[T].mean(1)
col = np.zeros((len(T), 3))
if img is not None:
    hh, ww = img.shape[:2]
    col = img[np.clip(((uvc[:, 1] % 1) * hh).astype(int), 0, hh - 1), np.clip(((uvc[:, 0] % 1) * ww).astype(int), 0, ww - 1)]
print('comps', [(int(c), int(cnt[c])) for c in comps[:6]])
print('shell', int(shell.sum()), 'under hair', int((shell & under).sum()), 'open', int((shell & ~under).sum()))
print('shell y', C[shell, 1].min().round(3), C[shell, 1].max().round(3), 'z', C[shell, 2].min().round(3), C[shell, 2].max().round(3))
np.savez(HERE / 'work' / 'head_survey.npz', comp=fl, shell=shell, hair=hair, under=under, ud=ud, col=col)
rgb = np.zeros((len(T), 3), int); rgb[:] = (60, 200, 60)
rgb[shell & ~under] = (220, 50, 50); rgb[shell & under] = (60, 90, 220); rgb[hair] = (240, 150, 40)
m = shell | hair
views(P, T[shell], rgb[shell], (-0.15, 0.15, 1.42, 1.82), HERE / 'review' / 'head_survey_shell.png', size=420)
views(P, T[m], rgb[m], (-0.15, 0.15, 1.42, 1.82), HERE / 'review' / 'head_survey.png', size=420)
