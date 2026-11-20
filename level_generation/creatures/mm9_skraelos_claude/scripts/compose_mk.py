#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paint: pads from inside the charts at 4K (Meshy's gutters), downsamples once. Writes textures/mk_body_raw.png (2K), mk_body_normal.png, mk_body_rough.png (1K). Args: <meshy job>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
J = Path('meshy') / sys.argv[1]; T = Path('textures')
D = np.load('work/uv_v1.npz'); tri, uv, mat = D['tri'], D['uv'], D['mat']
S = 4096
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in tri[mat == 0]: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
cov = np.asarray(cov) > 0; inner = ndimage.binary_erosion(cov, iterations=2)
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
for name, out, size, mode in (('base_color', 'raw', (2048, 2048), 'RGB'), ('normal', 'normal', (1024, 1024), 'RGB'), ('roughness', 'rough', (1024, 1024), 'L')):
    p = J / f'texture_urls_0_{name}.png'
    if not p.exists(): print('no', p); continue
    im = np.asarray(Image.open(p).convert(mode))
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]]
    Image.fromarray(im).resize(size, Image.LANCZOS).save(T / f'mk_body_{out}.png')
print('COMPOSE', J)
