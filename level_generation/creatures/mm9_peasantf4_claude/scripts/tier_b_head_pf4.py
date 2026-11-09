#!/usr/bin/env python3
"""Tier B head base (2026-11-02): MM9's PeasantF4b is another woman (dark-brown hair and braids, a greyer, worn cream veil) on the same head,
so tier B's head colour starts from tier A's fixed paint (one Meshy head retexture covers both: budget) and
- hair: every braid texel, and head-shell texels of the blonde paint (blue/red < 0.56, hue 18-60, saturation > 0.25) above the brows, are re-coloured
  dark brown with their luminance detail (MM9 F3b's hair 40/28/22 at the mid tone);
- veil and hood: tinted toward MM9 F3b's worn linen (x 0.93 / 0.89 / 0.80);
the face itself is repainted afterwards (Codex repaint projected by project_face_pf4.py).
Args: <in png (tier A fix)> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
Z0 = -0.9297
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
PART = np.full((S, S), -1, int); POS = np.zeros((S, S, 3))
for fi in np.where(mat == 1)[0]:
    q = uv[tri[fi]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int); PART[yy, xx] = comp[tri[fi][0]]; POS[yy, xx] = l3[ok] @ co[tri[fi]]
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
lum = im @ np.array([0.2126, 0.7152, 0.0722])
z = POS[..., 2] - Z0
pid = {n: i for i, n in enumerate(names)}
braid = PART == pid['braids']
br = im[..., 2] / np.maximum(im[..., 0], 1e-3)
hair = (PART == pid['head']) & (z > 1.63) & (br < 0.56) & (hue > 18) & (hue < 60) & (sat > 0.25)     # blonde: yellower than skin (blue/red < 0.56)
hair = ni.binary_closing(hair, iterations=2) & (PART == pid['head'])
hair = ni.binary_opening(hair, iterations=1) | braid
k = np.clip(ni.gaussian_filter(hair.astype(np.float32), 1.0) * 1.3, 0, 1)[..., None] * (PART >= 0)[..., None]
mid = float(np.median(lum[hair])) if hair.any() else 0.5
dark = np.array([40, 28, 22], np.float32) / 255 * np.clip(lum / mid, 0.35, 1.9)[..., None]
out = im * (1 - k) + np.clip(dark, 0, 1) * k
cloth = np.isin(PART, [pid['veil'], pid['scarf']])
out[cloth] = out[cloth] * np.array([0.93, 0.89, 0.80])
cov = PART >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('TIERB hair texels', int(hair.sum()), 'braid', int(braid.sum()), 'cloth', int(cloth.sum()))
