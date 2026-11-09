#!/usr/bin/env python3
"""One empty spot per set for the dark lining: the point of each layout farthest from any chart (PartUV). Writes work/dark_texel.json. Project folder."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Z = np.load('work/faces.npz'); UV, MAT = Z['uv'], Z['mat']
out = {}
for k, name in ((0, 'limbs'), (1, 'torso'), (2, 'head')):
    S = 1024; im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
    for t in UV[MAT == k]:
        d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
    m = np.asarray(im) > 0
    m[:, [0, -1]] = True; m[[0, -1], :] = True
    D = ndimage.distance_transform_edt(~m)
    y, x = np.unravel_index(D.argmax(), D.shape)
    out[name] = dict(u=float((x + .5) / S), v=float((y + .5) / S), r=float(D.max()))
json.dump(out, open('work/dark_texel.json', 'w'), indent=0); print('DARK', out)
