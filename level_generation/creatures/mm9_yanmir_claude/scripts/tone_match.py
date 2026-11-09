#!/usr/bin/env python3
"""Skin tone toward MM9's (compared by eye and by numbers: MM9's blue skin texels mean saturation 0.34, value 0.63; the Meshy body
paint 0.41 / 0.58, the head 0.37 / 0.60). Blue texels (soft mask on hue and saturation) get saturation x ks and value x kv.
Args: <in png> <out png> <ks> <kv>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
src, dst, ks, kv = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
a = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
mx = a.max(2); mn = a.min(2); s = (mx - mn) / np.maximum(mx, 1e-3)
blue = np.clip((a[..., 2] - a[..., 0] - 0.04) / 0.08, 0, 1) * np.clip((a[..., 2] - a[..., 1] + 0.02) / 0.04, 0, 1) * np.clip((s - 0.12) / 0.1, 0, 1)
blue = ndimage.gaussian_filter(blue, 1.5)
grey = mx[..., None]
out = grey + (a - grey) * (1 + (ks - 1) * blue[..., None])          # saturation about the value
out = out * (1 + (kv - 1) * blue[..., None])
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(dst)
print('TONE', dst, 'mask mean', round(float(blue.mean()), 3))
