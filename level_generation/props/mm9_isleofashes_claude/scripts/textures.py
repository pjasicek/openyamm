#!/usr/bin/env python3
"""Enlarges every prop's MM9 skin x4 with Lanczos, as a stopgap until the props' Codex x4 pass. No Real-ESRGAN: it was slow,
hogged the machine, and turned rope into shingles and canvas into moire, and the Codex pass replaces these anyway.
The skin is padded by 16 wrapped pixels per side (the UVs repeat, so tiles stay seamless), colour under transparent
texels is bled from the opaque ones, the result is cropped and lightly sharpened (unsharp 0.7 px, 50 %). Alpha is
enlarged bicubic and kept only where the skin has transparency.
Writes textures/<prop>_basecolor.png. Usage: textures.py [prop ...]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
PAD = 16


def bleed(rgba):
    """Fill transparent texels with the nearest opaque colour (no dark or magenta fringes after filtering)."""
    a = rgba[..., 3] > 127
    if a.all() or not a.any():
        return rgba[..., :3]
    _, (iy, ix) = ndimage.distance_transform_edt(~a, return_indices=True)
    return rgba[..., :3][iy, ix]


def upscale(src, out):
    rgba = np.array(Image.open(src).convert('RGBA'))
    rgb = bleed(rgba)
    padded = np.pad(rgb, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='wrap')
    h, w = rgb.shape[:2]
    big = Image.fromarray(padded).resize((padded.shape[1] * 4, padded.shape[0] * 4), Image.LANCZOS)
    big = big.crop((PAD * 4, PAD * 4, PAD * 4 + w * 4, PAD * 4 + h * 4))
    big = big.filter(ImageFilter.UnsharpMask(radius=0.7, percent=50, threshold=2))
    if (rgba[..., 3] < 250).any():
        alpha = Image.fromarray(rgba[..., 3]).resize((w * 4, h * 4), Image.BICUBIC)
        big = big.convert('RGBA'); big.putalpha(alpha)
    big.save(out, optimize=True)
    print('UPSCALED', src.name, rgb.shape[1], '->', big.size[0], out.name)


def main():
    props = sys.argv[1:] or sorted(p.name for p in (HERE / 'work/raw').iterdir() if not p.name.startswith('ref_'))
    (HERE / 'textures').mkdir(exist_ok=True)
    for prop in props:
        upscale(HERE / f'work/raw/{prop}/skins/{prop}.png', HERE / f'textures/{prop}_basecolor.png')


if __name__ == '__main__':
    main()
