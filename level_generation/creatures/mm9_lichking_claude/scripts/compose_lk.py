#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paint on the body atlas (project folder): pads from inside the charts at 4K (Meshy's gutters are smeared),
paints the coat lining (faces flagged in the uv npz) a plain dark navy carrying a quarter of the paint's own detail, then downsamples once:
colour 2048, normal / roughness / metallic 1024. Writes textures/lk_raw.png, lk_normal.png, lk_rough.png, lk_metal.png, lk_cov.png. Args: <meshy job>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
job = sys.argv[1]; J = Path('meshy') / job; T = Path('textures')
D = np.load('work/uv_v1.npz'); tri, uv, mat, lin = D['tri'], D['uv'], D['mat'], D['lining']
S = 4096
def raster(sel):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    for t in tri[sel]: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
    return np.asarray(im) > 0
cov = raster(mat == 0); lmask = ndimage.binary_dilation(raster((mat == 0) & lin), iterations=3) & cov
inner = ndimage.binary_erosion(cov, iterations=2)
idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
Image.fromarray((cov[::2, ::2] * 255).astype('u1')).save(T / 'lk_cov.png')
for name, out, size, mode in (('base_color', 'raw', 2048, 'RGB'), ('normal', 'normal', 1024, 'RGB'), ('roughness', 'rough', 1024, 'L'), ('metallic', 'metal', 1024, 'L')):
    p = J / f'texture_urls_0_{name}.png'
    if not p.exists(): print('no', p); continue
    im = np.asarray(Image.open(p).convert(mode))
    if im.shape[0] != S: im = np.asarray(Image.fromarray(im).resize((S, S), Image.LANCZOS))
    im = im[idx[0], idx[1]].copy()
    if name == 'base_color':
        f = im.astype(np.float32) / 255; lum = f.mean(-1, keepdims=True)
        loc = ndimage.gaussian_filter(lum[..., 0], 12)[..., None]
        lining = np.array([0.055, 0.065, 0.11]) * np.clip(1 + 0.25 * (lum - loc) / 0.1, 0.7, 1.3)
        f = np.where(lmask[..., None], lining, f); im = (np.clip(f, 0, 1) * 255 + .5).astype('u1')
    if name == 'normal': im = np.where(lmask[..., None], np.array([128, 128, 255], 'u1'), im)
    Image.fromarray(im).resize((size, size), Image.LANCZOS).save(T / f'lk_{out}.png')
print('COMPOSE', J, 'lining texels', int(lmask.sum()))
