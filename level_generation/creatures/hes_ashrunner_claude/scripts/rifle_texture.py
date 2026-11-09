#!/usr/bin/env python3
"""The rifle's texture and side profile from the HD prop reference (references_hd/rifle.png, side view, muzzle to
image right, true alpha): the alpha box cropped, transparent pixels filled with the nearest opaque colour, resized to
1024 x 256 -> textures/props/rifle.png and the runtime maps textures/har_rifle_{basecolor,normal,metal_rough}.png
(ORM: R specular mask 0.6 ceramic / 0.8 gold, G roughness 0.45 / 0.3, B 0); work/rifle_profile.json: per column the
alpha top/bottom rows (for make_rifle.py) and the crop box. Args: none"""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = Image.open(os.path.join(HERE, 'references_hd', 'rifle.png')).convert('RGBA')
im = np.asarray(src).astype(np.float64); al = im[..., 3] > 128
ys, xs = np.nonzero(al); box = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]
cols = {}
for x in range(box[0], box[1] + 1):
    c = np.nonzero(al[:, x])[0]
    if len(c):
        cols[x] = [int(c.min()), int(c.max())]
json.dump({'box': box, 'cols': cols}, open(os.path.join(HERE, 'work', 'rifle_profile.json'), 'w'))
crop = im[box[2]:box[3] + 1, box[0]:box[1] + 1]; ca = al[box[2]:box[3] + 1, box[0]:box[1] + 1]
_, (iy, ix) = ndimage.distance_transform_edt(~ca, return_indices=True)
rgb = crop[..., :3][iy, ix]
os.makedirs(os.path.join(HERE, 'textures', 'props'), exist_ok=True)
base = Image.fromarray(rgb.astype(np.uint8)).resize((1024, 256), Image.LANCZOS)
base.save(os.path.join(HERE, 'textures', 'props', 'rifle.png'))
T = os.path.join(HERE, 'textures'); base.save(os.path.join(T, 'har_rifle_basecolor.png'))
h, s, v = [np.asarray(c, np.float64) / 255 for c in base.convert('HSV').split()]
gold = (h * 360 > 25) & (h * 360 < 60) & (s > 0.4) & (v > 0.3)
Image.new('RGB', base.size, (128, 128, 255)).save(os.path.join(T, 'har_rifle_normal.png'))
orm = np.zeros(base.size[::-1] + (3,)); orm[..., 0] = np.where(gold, 0.8, 0.6); orm[..., 1] = np.where(gold, 0.3, 0.45)
Image.fromarray((orm * 255).astype(np.uint8)).save(os.path.join(T, 'har_rifle_metal_rough.png'))
print('RIFLETEX box', box, 'gold share', round(float(gold.mean()), 3))
