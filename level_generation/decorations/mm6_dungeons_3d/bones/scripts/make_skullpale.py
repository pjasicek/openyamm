#!/usr/bin/env python3
"""Inputs of build_skullpile_inst.py, written at SIZE:
- textures/skullpale_*: the Meshy skull's texture set (LOD0 skulls) with a grey-normalised base colour: luminance over
  its median, compressed, at PALE (its local detail only; COLOR_0 brings the sprite's colours);
- textures/proxypale_*: the same for the low-poly skull's bake (bake_skull_proxy.py; LOD1 skulls);
- work/sklplrev_native_tables.npz: the native sprite's sorted luminance and its smoothed luminance-to-colour table.
Usage: make_skullpale.py [size]"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 512
PALE = 0.88
LUMA = np.array([0.2126, 0.7152, 0.0722])
TEXTURES = os.path.join(HERE, 'textures')
MESHY = os.path.join(HERE, 'meshy', 'skull_retexture_v1')


def pale(source, prefix, normal, rough):
    base = np.asarray(Image.open(source).convert('RGB').resize((SIZE, SIZE), Image.LANCZOS), np.float64) / 255
    lum = base @ LUMA
    grey = np.clip(PALE * (lum / np.median(lum[lum > 0.05])) ** 0.8, 0, 1)
    Image.fromarray(np.round(np.repeat(grey[..., None], 3, -1) * 255).astype(np.uint8)).save(
        os.path.join(TEXTURES, f'{prefix}_basecolor.png'))
    Image.open(normal).convert('RGB').resize((SIZE, SIZE), Image.LANCZOS).save(
        os.path.join(TEXTURES, f'{prefix}_normal.png'))
    mr = np.zeros((SIZE, SIZE, 3), np.uint8); mr[..., 0] = 255; mr[..., 1] = round(rough * 255)   # bone: no metal
    Image.fromarray(mr).save(os.path.join(TEXTURES, f'{prefix}_mr.png'))
    print('PALE', prefix, SIZE, 'grey mean', round(float(grey.mean()), 3))


pale(os.path.join(MESHY, 'texture_urls_0_base_color.png'), 'skullpale', os.path.join(MESHY, 'texture_urls_0_normal.png'),
     0.87)
pale(os.path.join(HERE, 'work', 'skullproxy_base.png'), 'proxypale', os.path.join(HERE, 'work', 'skullproxy_normal.png'),
     0.87)

native = np.asarray(Image.open(os.path.join(HERE, 'native', 'sklplrev_native_embedded.png')).convert('RGBA'),
                    np.float64)
pixels = native[native[..., 3] > 0][:, :3] / 255
nlum = pixels @ LUMA
bins = np.linspace(0, 1, 33); centres = (bins[:-1] + bins[1:]) / 2
index = np.clip(np.digitize(nlum, bins) - 1, 0, 31)
table = np.array([pixels[index == k].mean(0) if (index == k).any() else [np.nan] * 3 for k in range(32)])
for c in range(3):
    good = ~np.isnan(table[:, c])
    table[:, c] = np.interp(centres, centres[good], table[good, c])
table = np.stack([np.convolve(np.pad(table[:, c], 1, mode='edge'), [0.25, 0.5, 0.25], 'valid') for c in range(3)], -1)
np.savez(os.path.join(HERE, 'work', 'sklplrev_native_tables.npz'), lum=np.sort(nlum), centres=centres, table=table)
