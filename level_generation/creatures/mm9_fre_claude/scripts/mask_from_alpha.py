#!/usr/bin/env python3
"""Transparent background for a Codex paint-over of a render: alpha from the same render made with a transparent film (exact silhouette,
1 px dilation, 0.7 px feather); colours bled outward. Args: <alpha render png> <codex output png> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ni
al = np.asarray(Image.open(sys.argv[1]).convert('RGBA'))[..., 3] > 8
out = Image.open(sys.argv[2]).convert('RGB')
if out.size != al.shape[::-1]: out = out.resize(al.shape[::-1], Image.LANCZOS)
o = np.asarray(out, np.float32)
fg = ni.binary_fill_holes(ni.binary_dilation(al, iterations=1))
a = np.asarray(Image.fromarray((fg * 255).astype('u1')).filter(ImageFilter.GaussianBlur(0.7)))
idx = ni.distance_transform_edt(~fg, return_distances=False, return_indices=True); o = o[idx[0], idx[1]]
Image.fromarray(np.dstack([o.astype('u1'), a])).save(sys.argv[3]); print('MASK', sys.argv[3], round(float(fg.mean()), 3))
