#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paint (project folder): pads from inside the charts at 4K (Meshy's gutters), downsamples once. Writes textures/nos_raw.png 2K, nos_normal.png, nos_rough.png 1K, work/cov_2k.npy. Args: <meshy job>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
job = sys.argv[1]; J = Path('meshy') / job; T = Path('textures')
D = np.load('work/uv_v1.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
S = 4096
lin = np.isin(comp[tri[:, 0]], [names.index('rlining'), names.index('slining')])
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in tri[(mat == 0) & ~lin]:
    dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
cov = np.asarray(cov) > 0
inner = ndimage.binary_erosion(cov, iterations=2)
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
np.save('work/cov_2k.npy', cov[::2, ::2])
for name, out, size, mode in (('base_color', 'raw', (2048, 2048), 'RGB'), ('normal', 'normal', (1024, 1024), 'RGB'), ('roughness', 'rough', (1024, 1024), 'L')):
    p = J / f'texture_urls_0_{name}.png'
    im = np.asarray(Image.open(p).convert(mode))
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]]
    Image.fromarray(im).resize(size, Image.LANCZOS).save(T / f'nos_{out}.png')
print('COMPOSE', J, 'cov', float(cov.mean()))
