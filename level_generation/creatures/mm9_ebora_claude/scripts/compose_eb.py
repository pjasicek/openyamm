#!/usr/bin/env python3
"""Runtime maps from a 4K Meshy paint on the one upload layout (project folder), downsampled once. Pads from inside the
charts at 4K (Meshy's gutters). Sets: torso = bottom half -> 2048x1024 colour, 1024x512 normal/rough; head = top-left
quarter -> 1024x1024 colour, 1024 normal/rough; legs = top-right quarter -> 1024x1024 colour, 512 normal/rough.
Writes textures/<pre>_<set>_{raw,normal,rough}.png. Args: <meshy job> <prefix>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
job, pre = sys.argv[1:3]
J = Path('meshy') / job; T = Path('textures'); T.mkdir(exist_ok=True)
D = np.load('work/uv_frozen.npz'); tri, uv = D['tri'], D['uv']
S = 4096
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in tri:
    dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
cov = np.asarray(cov) > 0
inner = ndimage.binary_erosion(cov, iterations=2)
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
H = S // 2
SETS = (('torso', (0, H, S, S), (2048, 1024), (1024, 512)), ('head', (0, 0, H, H), (1024, 1024), (1024, 1024)),
        ('legs', (H, 0, S, H), (1024, 1024), (512, 512)))
for name, out, mode in (('base_color', 'raw', 'RGB'), ('normal', 'normal', 'RGB'), ('roughness', 'rough', 'L'), ('metallic', 'metal', 'L')):
    p = J / f'texture_urls_0_{name}.png'
    if not p.exists(): print('no', p); continue
    im = np.asarray(Image.open(p).convert(mode))
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]]
    for part, box, csize, nsize in SETS:
        Image.fromarray(im).resize(csize if out == 'raw' else nsize, Image.LANCZOS, box=box).save(T / f'{pre}_{part}_{out}.png')
print('COMPOSE', J, pre)
