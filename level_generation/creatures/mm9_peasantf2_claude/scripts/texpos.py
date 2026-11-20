"""Texel -> rest position / face normal / part maps for one material of a mesh npz (shared by neck_seam_pf2.py).
texel_maps(npz_path, mat_id, size) -> dict(cov, pos, nrm, part, face) ; rows are image rows (v flipped)."""
import numpy as np
from PIL import Image, ImageDraw
def texel_maps(D, mat_id, S):
    co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']
    fi = np.where(mat == mat_id)[0]
    im_ = Image.new('I', (S, S), -1); dr = ImageDraw.Draw(im_)
    for k, f in enumerate(fi): dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=int(k))
    F = np.asarray(im_).astype(np.int64); cov = F >= 0
    yy, xx = np.nonzero(cov); f = fi[F[yy, xx]]
    P = np.stack([(xx + 0.5) / S, 1 - (yy + 0.5) / S], 1); Au, Bu, Cu = uv[tri[f, 0]], uv[tri[f, 1]], uv[tri[f, 2]]
    v0, v1, v2 = Bu - Au, Cu - Au, P - Au; d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01; den[np.abs(den) < 1e-14] = 1e-14; b1 = (d11 * d20 - d01 * d21) / den; b2 = (d00 * d21 - d01 * d20) / den
    b1 = np.clip(b1, 0, 1); b2 = np.clip(b2, 0, 1 - b1); b0 = 1 - b1 - b2
    pos = np.zeros((S, S, 3)); pos[yy, xx] = co[tri[f, 0]] * b0[:, None] + co[tri[f, 1]] * b1[:, None] + co[tri[f, 2]] * b2[:, None]
    fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    nrm = np.zeros((S, S, 3)); nrm[yy, xx] = fn[f]
    part = np.full((S, S), -1); part[yy, xx] = comp[tri[f, 0]]
    face = np.full((S, S), -1); face[yy, xx] = f
    return dict(cov=cov, pos=pos, nrm=nrm, part=part, face=face)
