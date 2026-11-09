#!/usr/bin/env python3
"""Coloured flame flipbooks for the fire decorations of every world, from the CC0 Unity Labs Flame02 flipbook (16 x 4
frames, a seamless 64-frame loop) with the recipe of ../mm6_dungeons_3d/scripts/make_flames.py. Each colour's ramp
(mean flame colour per brightness quantile) is measured on the native frames of an MM7 sprite with that flame, in the
flame's rows only (above the torch head or the brazier bowl). The orange flame stays
../mm6_dungeons_3d/textures/flame02_basecolor.png. Writes flame02_<colour>_basecolor.png here.
Usage: make_coloured_flames.py"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MM6 = HERE.parent / 'mm6_dungeons_3d'
sys.path.insert(0, str(MM6 / 'scripts'))
import make_flames  # noqa: E402

NATIVE = REPO / 'assets_dev/_legacy/sprites_original'
# colour: (native sprite whose frames <sprite>a..h show the flame, flame rows as a fraction of the frame height)
COLOURS = {
    'red': ('torch07', 0.42),
    'purple': ('torch05', 0.42),
    'green': ('torch06', 0.42),
    'blue': ('dec60', 0.36),
    'white': ('dec63', 0.36),
}


def native_ramp(sprite, flame_rows, bins=32):
    samples = []
    for frame in 'abcdefgh':
        path = NATIVE / f'{sprite}{frame}.bmp'
        if not path.exists():
            continue
        rgb = np.asarray(Image.open(path).convert('RGB'), dtype=np.float64)
        key = rgb[0, 0].copy()
        flame = rgb[:int(rgb.shape[0] * flame_rows)].reshape(-1, 3)
        flame = flame[(np.abs(flame - key).sum(axis=1) > 0) & (make_flames.luminance(flame) > 0.12)]
        samples.append(flame)
    rgb = np.concatenate(samples)
    # Equal-count bins (brightness quantiles of the native flame pixels), so the flame body takes the sprite's
    # dominant colours; equal-range bins gave the rare highlights most of the body (red read as salmon).
    order = np.argsort(make_flames.luminance(rgb))
    ramp = np.array([rgb[chunk].mean(axis=0) for chunk in np.array_split(order, bins)])
    return ramp


def main():
    source, fade_low, fade_high = make_flames.FLAMES['flame02']
    sheet = Image.open(MM6 / 'source/unity_labs_vfx' / source)
    previews = []
    for colour, (sprite, rows) in COLOURS.items():
        ramp = native_ramp(sprite, rows)
        out = HERE / f'flame02_{colour}_basecolor.png'
        coloured = make_flames.recolour(sheet, ramp, fade_low, fade_high)
        coloured.save(out, optimize=True)
        previews.append(coloured.crop((0, 0, coloured.width // 4, coloured.height // 4)))
        print(f'{colour}: ramp from {sprite} {ramp[0].round()} .. {ramp[-1].round()} -> {out.relative_to(REPO)}')
    preview = Image.new('RGBA', (sum(image.width for image in previews), previews[0].height), (30, 30, 30, 255))
    x = 0
    for image in previews:
        preview.alpha_composite(image, (x, 0))
        x += image.width
    preview.save(HERE / 'preview.png')


if __name__ == '__main__':
    main()
