#!/usr/bin/env python3
"""Texture sets of the heaps and small props: textures/misc_<name>_{basecolor,normal,mr}.png from the CC0 Poly
Haven sets in textures/source/ (small_fetch.py). Base colour: the scan's diffuse, optionally through a colour
(the scan's luminance, normalised to its mean, times a target sRGB colour, with a contrast power), saturation and gain;
normal: the OpenGL normal map, optionally flattened; mr: G = roughness remapped to [lo, hi], B = metal.
Usage: small_textures.py [name ...]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / 'textures' / 'source'
OUT = HERE / 'textures'

# name: source asset, size, colour (None keeps the scan's), contrast, saturation, gain, normal strength,
# roughness range, metal, blur of the luminance (pixels, before the colour)
SPECS = {
    'gold': dict(asset='rusty_metal_02', size=256, colour=(200, 184, 128), contrast=0.35, blur=3.0,
                 normal=0.35, rough=(0.3, 0.55), metal=0.0),
    'goldout': dict(asset='rusty_metal_02', size=512, colour=(226, 168, 72), contrast=0.8, blur=2.0,
                    normal=0.35, rough=(0.3, 0.55), metal=0.0),
    'vase': dict(asset='rusty_metal_02', size=512, contrast=1.3, two_tone=((112, 118, 128), (200, 140, 60), 0.4, 0.12), normal=0.6,
                 rough=(0.45, 0.8), metal=0.0, blur=1.0),
    'driftwood': dict(nsize=512, msize=128, asset='bark_platanus', size=512, saturation=1.0, gain=1.0, normal=1.0, rough=(0.7, 0.95),
                      metal=0.0),
    'gravel': dict(nsize=512, msize=128, asset='gravelly_sand', size=512, saturation=0.75, normal=1.0, rough=(0.8, 1.0), metal=0.0),
    'soil': dict(nsize=512, msize=128, asset='brown_mud_rocks_01', size=512, normal=1.0, rough=(0.75, 1.0), metal=0.0),
    'mound': dict(nsize=512, msize=128, asset='brown_mud_dry', size=512, normal=1.0, rough=(0.75, 1.0), metal=0.0),
    'barrel': dict(nsize=512, msize=128, asset='wooden_barrel', size=512, normal=1.0, rough=(0.6, 0.95), metal=0.0),
    'planks': dict(nsize=256, msize=128, asset='weathered_planks', size=512, normal=1.0, rough=(0.65, 0.95), metal=0.0),
    'rustiron': dict(nsize=256, msize=128, asset='rusty_metal_05', size=512, normal=1.0, rough=(0.55, 0.9), metal=0.0),
    'greenmetal': dict(nsize=256, msize=128, asset='green_metal_rust', size=512, normal=1.0, rough=(0.5, 0.85), metal=0.0),
    'rock': dict(nsize=256, msize=128, asset='rock_boulder_dry', size=512, saturation=0.7, normal=1.0, rough=(0.7, 0.95), metal=0.0),
    'mossrock': dict(nsize=256, msize=128, asset='rock_pitted_mossy', size=512, normal=1.0, rough=(0.7, 0.95), metal=0.0),
    'cloth': dict(nsize=256, msize=128, asset='dirty_carpet', size=512, colour=(120, 30, 24), contrast=1.0, normal=1.0,
                  rough=(0.85, 1.0), metal=0.0),
}


def load(asset, kind, size):
    return Image.open(SRC / asset / f'{asset}_{kind}_1k.png').convert('RGB').resize((size, size), Image.LANCZOS)


def make(name):
    s = SPECS[name]
    size = s['size']
    diff = load(s['asset'], 'diff', size)
    if s.get('blur'):
        diff = diff.filter(ImageFilter.GaussianBlur(s['blur']))
    rgb = np.asarray(diff).astype(np.float32) / 255.0
    if s.get('colour'):
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        lum = (lum / lum.mean()) ** s.get('contrast', 1.0)
        rgb = np.clip(lum[..., None] * np.array(s['colour'], np.float32) / 255.0, 0, 1)
    if s.get('two_tone'):
        # Neutral metal (the scan's luminance) and copper rust where the scan is rusty (its saturation).
        metal, rust, threshold, spread = s['two_tone']
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        satur = rgb.max(2) - rgb.min(2)
        mask = np.clip((satur - threshold) / spread, 0, 1)
        mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)))
        mask = mask.astype(np.float32)[..., None] / 255.0
        shade = (lum / lum.mean())[..., None] ** s.get('contrast', 0.6)
        rgb = np.clip(shade * ((1 - mask) * np.array(metal) + mask * np.array(rust)) / 255.0, 0, 1)
    sat = s.get('saturation', 1.0)
    if sat != 1.0:
        grey = (rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
        rgb = grey + (rgb - grey) * sat
    rgb = np.clip(rgb * s.get('gain', 1.0), 0, 1)
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(OUT / f'misc_{name}_basecolor.png')
    nsize, msize = s.get('nsize', size), s.get('msize', size)
    nor = np.asarray(load(s['asset'], 'nor_gl', nsize)).astype(np.float32) / 127.5 - 1.0
    k = s.get('normal', 1.0)
    nor[..., :2] *= k
    nor /= np.linalg.norm(nor, axis=2, keepdims=True)
    Image.fromarray(((nor + 1) * 127.5 + 0.5).clip(0, 255).astype(np.uint8)).save(OUT / f'misc_{name}_normal.png')
    rough = np.asarray(load(s['asset'], 'rough', msize).convert('L')).astype(np.float32) / 255.0
    lo, hi = s['rough']
    rough = lo + (hi - lo) * (rough - rough.min()) / max(1e-6, rough.max() - rough.min())
    mr = np.zeros((msize, msize, 3), np.float32)
    mr[..., 1] = rough; mr[..., 2] = s['metal']
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(OUT / f'misc_{name}_mr.png')
    print('TEXTURE', name, 'mean', (rgb.reshape(-1, 3).mean(0) * 255).round().astype(int).tolist())


# Unique lathe textures (u once around, v 0..1 along the profile): a tileable set repeated (ru x rv) times, its base
# colour times a painted metal reflection, a function of u (vertical bright and dark bands, as the sprites' studio
# reflections) and v (bright rims), so the turned props read metallic under the dungeon's diffuse-only light.
LATHE = {
    'goblet_lathe': dict(source='gold', repeat=(2, 2), base=0.62,
                   u_bands=[(0.14, 0.018, 1.0), (0.19, 0.025, 0.55), (0.29, 0.013, 0.7), (0.38, 0.03, -0.35)],
                   v_bands=[]),
    'vase_lathe': dict(source='vase', repeat=(2, 2), base=0.55,
                 u_bands=[(0.16, 0.015, 1.3), (0.20, 0.035, 0.5), (0.35, 0.02, 0.6), (0.43, 0.03, -0.3)],
                 v_bands=[]),
}


def make_lathe(name):
    s = LATHE[name]
    ru, rv = s['repeat']
    result = {}
    for kind in ('basecolor', 'normal', 'mr'):
        a = np.asarray(Image.open(OUT / f"misc_{s['source']}_{kind}.png").convert('RGB'))
        result[kind] = np.tile(a, (rv, ru, 1))
    h, w = result['basecolor'].shape[:2]
    uu = (np.arange(w) + 0.5) / w
    vv = 1 - (np.arange(h) + 0.5) / h                    # image rows top to bottom = v 1..0
    f = np.full((h, w), s['base'], np.float32)
    for c, width, amp in s['u_bands']:                  # period 0.5: the pattern repeats twice around
        x = uu % 0.5
        d = np.minimum(abs(x - c), 0.5 - abs(x - c))
        f += amp * np.exp(-(d / width) ** 2)[None, :]
    for c, width, amp in s['v_bands']:
        f += amp * np.exp(-((vv - c) / width) ** 2)[:, None]
    rgb = result['basecolor'].astype(np.float32) / 255.0
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4) * np.clip(f, 0.1, 3)[..., None]
    lin = np.clip(lin / lin.max(), 0, 1)
    out = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(OUT / f'misc_{name}_basecolor.png')
    for kind in ('normal', 'mr'):
        Image.fromarray(result[kind]).save(OUT / f'misc_{name}_{kind}.png')
    print('LATHE', name, (w, h), 'mean', (out.reshape(-1, 3).mean(0) * 255).round().astype(int).tolist())


if __name__ == '__main__':
    for n in sys.argv[1:] or list(SPECS) + list(LATHE):
        (make if n in SPECS else make_lathe)(n)
