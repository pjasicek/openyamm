#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paint on the one upload layout (project folder). Pads from inside the charts at 4K (Meshy's gutters), downsamples once: Up = top half, Low = bottom half, each 2048x1024 colour, 1024x512 normal and roughness.
Writes textures/es_{up,low}_raw.png, es_{up,low}_normal.png, es_{up,low}_rough.png. Args: <meshy job> <prefix>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
job, pre = sys.argv[1:3]
J = Path('meshy') / job; T = Path('textures')
D = np.load('work/uv_v1.npz'); tri, uv, mat = D['tri'], D['uv'], D['mat']
S = 4096
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in tri[mat != 2]:
    dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
cov = np.asarray(cov) > 0
inner = ndimage.binary_erosion(cov, iterations=2)
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
np.save('work/cov_4k.npy', cov[::2, ::2])
for name, out, size, mode in (('base_color', 'raw', (2048, 1024), 'RGB'), ('normal', 'normal', (1024, 512), 'RGB'), ('roughness', 'rough', (1024, 512), 'L'), ('metallic', 'metal', (1024, 512), 'L')):
    p = J / f'texture_urls_0_{name}.png'
    if not p.exists(): print('no', p); continue
    im = np.asarray(Image.open(p).convert(mode))
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]]
    for part, box in (('up', (0, 0, S, S // 2)), ('low', (0, S // 2, S, S))):
        Image.fromarray(im).resize(size, Image.LANCZOS, box=box).save(T / f'{pre}_{part}_{out}.png')
print('COMPOSE', J)
