"""Part id per texel (nearest-filtered) of one set from work/uv_dump.npz. Args: <set body|head> <size> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
SET, S, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
D = np.load('work/uv_dump.npz'); uvc, mat, part = D['uvc'], D['mat'], D['part']; M = 0 if SET == 'body' else 1
im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
for t, p in zip(uvc[mat == M], part[mat == M]): dr.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=int(p))
a = np.asarray(im); idx = ndimage.distance_transform_edt(a == 0, return_distances=False, return_indices=True)
Image.fromarray(a[idx[0], idx[1]]).save(OUT); print('PARTMAP', SET, np.unique(a).tolist())
