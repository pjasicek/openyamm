#!/usr/bin/env python3
"""The largest free square in the head atlas (1024): the mouth bag's dark patch. Writes scripts/bag_rect.json [x, y, size] (image pixels, y down). Run from the project folder."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
d = np.load('work/uv_v1.npz')
SZ = 1024
im = Image.new('L', (SZ, SZ), 0); dr = ImageDraw.Draw(im)
for t in d['Head_uv']:
    dr.polygon([(float(u * SZ), float((1 - v) * SZ)) for u, v in t], fill=255)
m = np.asarray(im) == 0
m = m.copy(); m[0, :] = m[-1, :] = False; m[:, 0] = m[:, -1] = False
free = ndimage.distance_transform_edt(m)
cy, cx = np.unravel_index(free.argmax(), free.shape)
rad = min(float(free.max()) - 2, 22.0)
rect = [int(cx - rad), int(cy - rad), int(2 * rad)]
json.dump(rect, open('scripts/bag_rect.json', 'w'))
print('BAG rect', rect, 'free', float(free.max()))
