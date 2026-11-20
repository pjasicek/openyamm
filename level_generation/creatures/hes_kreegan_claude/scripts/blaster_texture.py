#!/usr/bin/env python3
"""Blaster texture from the HD prop reference (references_hd/blaster.png, side view, muzzle to image right): the
alpha box cropped and resized to 512 x 256 -> textures/props/blaster.png (make_blaster.py maps the prop's side
projection onto exactly this box); transparent pixels filled with the nearest opaque colour (no background bleed).
Args: none"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
im = np.asarray(Image.open(os.path.join(HERE, 'references_hd', 'blaster.png')).convert('RGBA')).astype(np.float64)
al = im[..., 3] > 128
ys, xs = np.nonzero(al); im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; al = al[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
_, (iy, ix) = ndimage.distance_transform_edt(~al, return_indices=True)
rgb = im[..., :3][iy, ix]
os.makedirs(os.path.join(HERE, 'textures', 'props'), exist_ok=True)
Image.fromarray(rgb.astype(np.uint8)).resize((512, 256), Image.LANCZOS).save(os.path.join(HERE, 'textures', 'props', 'blaster.png'))
print('BLASTERTEX crop', xs.min(), xs.max(), ys.min(), ys.max())
# runtime maps for the attachment material (export_actor.py 'Blaster_A'): base colour, a flat normal map, and the
# ORM-packed specular mask / roughness: brown wood grip (saturated warm texels) R 0.25 G 0.6, metal R 0.6 G 0.35; B 0
base = Image.open(os.path.join(HERE, 'textures', 'props', 'blaster.png')).convert('RGB')
T = os.path.join(HERE, 'textures'); base.save(os.path.join(T, 'hgd_blaster_basecolor.png'))
h, s, v = [np.asarray(c, np.float64) / 255 for c in base.convert('HSV').split()]
wood = (h * 360 < 40) & (s > 0.35) & (v > 0.15)
Image.new('RGB', base.size, (128, 128, 255)).save(os.path.join(T, 'hgd_blaster_normal.png'))
orm = np.zeros(base.size[::-1] + (3,)); orm[..., 0] = np.where(wood, 0.25, 0.6); orm[..., 1] = np.where(wood, 0.6, 0.35)
Image.fromarray((orm * 255).astype(np.uint8)).save(os.path.join(T, 'hgd_blaster_metal_rough.png'))
print('BLASTERMAPS wood share', round(float(wood.mean()), 3))
