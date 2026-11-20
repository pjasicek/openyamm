#!/usr/bin/env python3
"""Props atlas (material TridentProps, 2048x1024): trident crop of references_hd/05_trident.png (planar projection, UVs from
make_trident.py), shin wrap swatch 06_wrap.png, tongue painted here from MM9's IMP3 tongue colours (no image-model return:
a smooth red ramp with a centre groove and pores). Writes textures/imp_props_basecolor.png, _normal.png (flat + wrap and
tongue relief from luminance), _orm.png (R 255, G roughness, B metallic: steel 0.7, brass 0.5, wood 0, leather 0)."""
import numpy as np
from PIL import Image
from scipy import ndimage
W, H = 2048, 1024
base = np.zeros((H, W, 3), np.float32)
rough = np.full((H, W), 0.7, np.float32)
metal = np.zeros((H, W), np.float32)
# trident: rows 370..645 of the 1536x1024 master at 4/3
t = Image.open('references_hd/05_trident.png').convert('RGBA')
t = t.crop((0, 370, 1536, 646)).resize((2048, 368), Image.LANCZOS)
a = np.asarray(t, np.float32) / 255
rgb, al = a[..., :3], a[..., 3] > 0.5
_, (iy, ix) = ndimage.distance_transform_edt(~al, return_indices=True)
rgb = rgb[iy, ix]
base[:368] = rgb
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
mx, mn = rgb.max(2), rgb.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
steel = (sat < 0.3) | (b > r)
brass = (~steel) & (r > g) & (g > b * 1.15) & (mx > 0.55)
wood = ~(steel | brass)
rough[:368][wood] = 0.72; rough[:368][steel] = 0.38; rough[:368][brass] = 0.42
metal[:368][steel] = 0.7; metal[:368][brass] = 0.5
gem = (r > 0.45) & (g < 0.3) & (b < 0.35)
rough[:368][gem] = 0.3; metal[:368][gem] = 0
# wrap: 1024 x 656 swatch below
wr = Image.open('references_hd/06_wrap.png').convert('RGB').resize((1024, 656), Image.LANCZOS)
wa = np.asarray(wr, np.float32) / 255
base[368:1024, :1024] = wa
lum = wa @ np.array([0.2126, 0.7152, 0.0722], np.float32)
rough[368:1024, :1024] = np.where(lum > 0.3, 0.42, 0.68)
metal[368:1024, :1024] = np.where(lum > 0.3, 0.55, 0.0)
# tongue: 512 x 656 painted, root at the top
tw, th = 512, 656
yy, xx = np.mgrid[0:th, 0:tw]
u = (xx - tw / 2) / (tw / 2); v = yy / th
rng = np.random.default_rng(3)
pores = ndimage.gaussian_filter(rng.standard_normal((th, tw)), 2.2)
pores = pores / pores.std()
groove = np.exp(-(u / 0.07) ** 2) * (0.55 + 0.45 * np.cos(v * 3))
c0, c1 = np.array([0.20, 0.015, 0.025]), np.array([0.70, 0.075, 0.09])
sh = np.clip(0.25 + 0.75 * (1 - u ** 2) * (0.55 + 0.45 * v), 0, 1) * (1 - 0.65 * groove)
col = c0 + (c1 - c0) * sh[..., None]
col = col * (1 + 0.1 * pores[..., None])
base[368:1024, 1024:1536] = np.clip(col, 0, 1)
rough[368:1024, 1024:1536] = 0.32
# normal
nz = np.zeros((H, W), np.float32)
nz[368:1024, :1024] = ndimage.gaussian_filter(lum, 1.0) * 1.2
nz[368:1024, 1024:1536] = sh * 0.8 + pores * 0.02
gy, gx = np.gradient(nz)
n = np.dstack([-gx * 6, gy * 6, np.ones_like(nz)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
nrm = ((n * 0.5 + 0.5) * 255).astype(np.uint8)
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save('textures/imp_props_basecolor.png')
Image.fromarray(nrm).save('textures/imp_props_normal.png')
orm = np.dstack([np.full((H, W), 255, np.uint8), (rough * 255).astype(np.uint8), (metal * 255).astype(np.uint8)])
Image.fromarray(orm).save('textures/imp_props_orm.png')
print('PROPS', {k: int(v.sum()) for k, v in dict(steel=steel, brass=brass, wood=wood, gem=gem).items()})
