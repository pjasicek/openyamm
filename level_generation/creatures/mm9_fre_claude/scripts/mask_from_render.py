#!/usr/bin/env python3
"""Transparent background for a Codex repaint of a render (pass 5): the silhouette is taken from the INPUT render (its flat background is
one colour), dilated by 1 px and feathered, so the alpha matches the 3D outline the repaint keeps. Colours are bled into the background.
Args: <input render png> <codex output png> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ni
src = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32)
out = Image.open(sys.argv[2]).convert('RGB')
if out.size != Image.open(sys.argv[1]).size:
    out = out.resize(Image.open(sys.argv[1]).size, Image.LANCZOS)
o = np.asarray(out, np.float32)
bg = np.median(np.concatenate([src[:8].reshape(-1, 3), src[:, :8].reshape(-1, 3), src[:, -8:].reshape(-1, 3)]), 0)
fg = np.abs(src - bg).sum(-1) > 6
lab, n = ni.label(fg); sz = ni.sum(fg, lab, range(1, n + 1)); fg = np.isin(lab, 1 + np.where(sz > 2000)[0])
fg = ni.binary_fill_holes(ni.binary_dilation(fg, iterations=1))
a = np.asarray(Image.fromarray((fg * 255).astype('u1')).filter(ImageFilter.GaussianBlur(0.7)))
idx = ni.distance_transform_edt(~fg, return_distances=False, return_indices=True); o = o[idx[0], idx[1]]
Image.fromarray(np.dstack([o.astype('u1'), a])).save(sys.argv[3]); print('MASK', sys.argv[3], round(float(fg.mean()), 3))
