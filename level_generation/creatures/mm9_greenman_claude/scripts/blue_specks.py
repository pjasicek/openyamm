#!/usr/bin/env python3
"""Remove lilac/blue specks Meshy painted on the head set's leaves and neck (mm9_greenman r4: two patches, 95 and 153 texels,
read as blue dots on the shoulder mantle in 3/4): blobs of texels with blue above red and green by 10+ and luminance under 140
(the eye whites are brighter and stay), dilated 2 px, are filled from the nearest unmasked texels and blurred 1 px.
Usage (project folder): blue_specks.py <png>   (in place)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
p = sys.argv[1]
a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
lum = a @ np.array([0.299, 0.587, 0.114])
m = (a[..., 2] > a[..., 1] + 6) & (a[..., 2] > a[..., 0] + 6) & (a[..., 2] > 60) & (lum < 140)
lab, n = ndimage.label(m)
keep = np.zeros_like(m)
for i in range(1, n + 1):
    if (lab == i).sum() >= 3:
        keep |= lab == i
# pass 2 (orchestrator: still visible beside the neck): each blob grown by 4 px takes the median colour of the ring
# 4-9 px round it (the nearest-texel fill of pass 1 copied the blob's own lilac halo and left a grey-white dot), plus the
# ring's own fine luminance texture shifted in
lab2, n2 = ndimage.label(ndimage.binary_dilation(keep, iterations=7))
out = a.copy()
for i in range(1, n2 + 1):
    blob = lab2 == i
    ring = ndimage.binary_dilation(blob, iterations=5) & ~blob & ~m
    if ring.sum() < 10:
        continue
    med = np.median(a[ring], 0)
    ys, xs = np.nonzero(blob); ry, rx = np.nonzero(ring)
    k = np.random.default_rng(i).integers(0, len(ry), len(ys))
    detail = (a[ry[k], rx[k]] - med) * 0.6
    out[ys, xs] = med + detail
keep = lab2 > 0
bl = ndimage.gaussian_filter(out, (0.7, 0.7, 0)); out[keep] = bl[keep]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(p)
print('BLUESPECKS texels', int(keep.sum()))
