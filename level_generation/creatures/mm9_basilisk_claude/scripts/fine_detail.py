#!/usr/bin/env python3
"""Fine detail of a base colour on the surface: luminance RMS of the 1-4 texel band (difference of Gaussians) inside
the islands, per region of the approved mask, as the viewer samples it (tier texture). Usage: fine_detail.py <uv3d npz>
<png> [...] pairs of layout and texture."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

for npz, png in zip(sys.argv[1::2], sys.argv[2::2]):
    d = np.load(npz)
    img = np.asarray(Image.open(png).convert('L'), np.float32)
    S = img.shape[0]
    cover = np.zeros((S, S), np.uint8)
    from PIL import ImageDraw
    canvas = Image.new('L', (S, S), 0)
    draw = ImageDraw.Draw(canvas)
    for t in d['uv']:
        draw.polygon([(u * S, (1 - v) * S) for u, v in t], fill=255)
    inner = ndimage.binary_erosion(np.asarray(canvas) > 0, iterations=4)
    band = ndimage.gaussian_filter(img, 1.0) - ndimage.gaussian_filter(img, 4.0)
    print(png, 'band RMS %.2f, interior %.1f%% of the atlas' % (float(np.sqrt((band[inner] ** 2).mean())), 100 * inner.mean()))
