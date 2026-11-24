#!/usr/bin/env python3
"""Xeen cutout textures: the colour under their transparent texels (F44, the player's pins 2026-11-24).

The surface cook (tools/cook_surface_textures.py) box-filters a straight-alpha mip chain, so in the smaller mips a
bar's edge texel averages its own colour with the colour stored under the transparent texels beside it. Xeen's cutout
textures were keyed from magenta, and the dark magenta left under their holes showed as magenta specks along the bars
of XD-08's portcullis (`xkportc`) whenever it was seen from a few steps away; the upscaled masters also kept a rim of
opaque magenta-tinted texels (the key's halo) round every hole. The fix is in the art: the halo (opaque texels within
two of a hole whose colour is magenta: red and blue over 40, green under 0.6 of both) becomes transparent, unless
magenta is the texture's own colour (over a fifth of its opaque texels, as the purple force field `xufield`); then the
colour under every transparent texel is bled outward from the nearest opaque texels, so filtering only ever mixes the
bars' own colours.

Usage: tools/xeen/texture_alpha_bleed.py [--check | --write]   (default --check: exit 1 when a texture needs it)
Covers assets_source/worlds/xeen/textures_x4/*.png (the desktop cook's masters) and assets_dev/worlds/xeen/textures_x2.
Status 2026-11-24: found, applied, then reverted (the six textures are dependencies of 23 lighting bakes, outdoor
maps among them): apply with the next bakes of those maps. After --write, recook the changed masters: tools/cook_surface_textures.py --profile desktop --only 'xeen/<stem>'.
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FOLDERS = [f'{R}/assets_source/worlds/xeen/textures_x4', f'{R}/assets_dev/worlds/xeen/textures_x2']
NEAR = 8          # texels from an opaque texel that a mip chain down to 1/8 size mixes in
TOLERANCE = 24    # largest channel difference from the bled colour still accepted


def bleed(rgba):
    """The image with every alpha-0 texel's colour taken from its nearest opaque texels (alpha kept)."""
    rgb = rgba[..., :3].astype(np.float64)
    known = rgba[..., 3] > 0
    out = rgb.copy()
    out[~known] = 0
    filled = known.copy()
    distance = np.full(known.shape, -1, dtype=np.int32)
    distance[known] = 0
    step = 0
    while not filled.all():
        step += 1
        total = np.zeros_like(out)
        count = np.zeros(known.shape)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                shifted = np.roll(np.roll(filled, dy, 0), dx, 1)
                total += np.roll(np.roll(out, dy, 0), dx, 1) * shifted[..., None]
                count += shifted
        grow = ~filled & (count > 0)
        if not grow.any():
            break
        out[grow] = total[grow] / count[grow][:, None]
        filled |= grow
        distance[grow] = step
    result = rgba.copy()
    result[..., :3] = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    result[known] = rgba[known]
    return result, distance


def magenta(rgb):
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    low = np.minimum(r, b)
    return (low > 40) & (g < 0.6 * low)


def halo(rgba):
    """Opaque texels within two of a transparent one whose colour is the magenta key's halo."""
    opaque = rgba[..., 3] > 0
    tinted = magenta(rgba[..., :3]) & opaque
    if tinted.sum() > 0.2 * opaque.sum():
        return np.zeros_like(opaque)
    near = np.zeros_like(opaque)
    hidden = ~opaque
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            near |= np.roll(np.roll(hidden, dy, 0), dx, 1)
    return tinted & near


def textures():
    for folder in FOLDERS:
        for path in sorted(glob.glob(f'{folder}/*.png')):
            image = Image.open(path)
            if 'A' not in image.getbands() and not (image.mode == 'P' and 'transparency' in image.info):
                continue
            rgba = np.asarray(image.convert('RGBA'))
            if (rgba[..., 3] == 0).sum() == 0 or (rgba[..., 3] > 0).sum() == 0:
                continue
            yield path, rgba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    bad = 0
    for path, rgba in textures():
        rim = halo(rgba)
        source = rgba.copy()
        source[rim, 3] = 0
        bled, distance = bleed(source)
        near = (rgba[..., 3] == 0) & (distance > 0) & (distance <= NEAR)
        diff = np.abs(bled[..., :3].astype(int) - rgba[..., :3].astype(int)).max(axis=2)
        off = int((near & (diff > TOLERANCE)).sum()) + int(rim.sum())
        rel = os.path.relpath(path, R)
        if off == 0:
            print(f'ok    {rel}')
            continue
        bad += 1
        if a.write:
            Image.fromarray(bled, 'RGBA').save(path)
            print(f'bled  {rel}: {int(rim.sum())} halo texels cleared; {off - int(rim.sum())} transparent texels near the '
                  f'opaque ones carried a foreign colour')
        else:
            print(f'FAIL  {rel}: {int(rim.sum())} magenta halo texels; {off - int(rim.sum())} transparent texels near the opaque '
                  f'ones carry a foreign colour '
                  f'(texture_alpha_bleed.py --write, then recook)')
    if bad and not a.write:
        sys.exit(1)


if __name__ == '__main__':
    main()
