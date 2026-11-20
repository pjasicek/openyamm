#!/usr/bin/env python3
"""Runtime maps from a 4K Meshy paint on our UVs (from mm9_peasantf8_claude/scripts/compose_pf.py): pads from inside the charts at 4K
(Meshy's gutters), downsamples once. Args: <meshy job> <set: body|head> -> textures/kira_<set>_raw.png (body 2K, head 2K: resized
to 1K or kept by the finish step), _normal.png, _rough.png, _metal.png (1K)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
J = Path('meshy') / sys.argv[1]; SET = sys.argv[2]; T = Path('textures'); T.mkdir(exist_ok=True)
D = np.load('work/uv_dump.npz'); uvc, mat = D['uvc'], D['mat']; M = 0 if SET == 'body' else 1
S = 4096
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in uvc[mat == M]: dr.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=255)
cov = np.asarray(cov) > 0; inner = ndimage.binary_erosion(cov, iterations=2)
Image.fromarray((cov * 255).astype('u1')).resize((1024, 1024), Image.BILINEAR).save(T / f'kira_{SET}_cover.png')
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
CS = (2048, 2048)
for name, out, size, mode in (('base_color', 'raw', CS, 'RGB'), ('normal', 'normal', (1024, 1024), 'RGB'), ('roughness', 'rough', (1024, 1024), 'L'),
                              ('metallic', 'metal', (1024, 1024), 'L')):
    p = J / f'texture_urls_0_{name}.png'
    if not p.exists(): print('no', p); continue
    im = np.asarray(Image.open(p).convert(mode)); print(name, im.shape)
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]]
    Image.fromarray(im).resize(size, Image.LANCZOS).save(T / f'kira_{SET}_{out}{"_dx" if out == "normal" else ""}.png')
print('COMPOSE', J, SET)
