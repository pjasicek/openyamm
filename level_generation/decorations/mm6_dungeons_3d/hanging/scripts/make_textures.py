#!/usr/bin/env python3
"""Textures of this batch: candle wax (a cream white with soft vertical drips, tileable; tinted per model through
COLOR_0) and brightened copies of the props `bone` and `skull` textures (../../../mm6_new_sorpigal_3d/props/textures,
read only; their normal and metal-roughness maps copied unchanged), whose means are darker than the native bones, so
the COLOR_0 tints stay at or below one. The candle flames use the shared flame03 flipbook (../../textures).
Writes textures/wax_basecolor.png, bonelight_*.png, skulllight_*.png. Usage: make_textures.py"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
PROPS_TEXTURES = HERE.parents[1] / 'mm6_new_sorpigal_3d' / 'props' / 'textures'
GAIN = 4.0          # linear gain: bone mean (98, 85, 59) -> about (186, 163, 117)


def brighten(source, name):
    image = np.asarray(Image.open(PROPS_TEXTURES / f'{source}_basecolor.png').convert('RGB')).astype(np.float64) / 255
    linear = np.where(image <= 0.04045, image / 12.92, ((image + 0.055) / 1.055) ** 2.4) * GAIN
    linear = linear / (1 + np.maximum(linear - 0.8, 0) * 0.8)          # soft shoulder instead of a hard clip
    srgb = np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.clip(linear, 0, 1) ** (1 / 2.4) - 0.055)
    Image.fromarray((np.clip(srgb, 0, 1) * 255).round().astype(np.uint8), 'RGB').save(
        HERE / 'textures' / f'{name}_basecolor.png', optimize=True)
    for kind in ('normal', 'mr'):
        shutil.copyfile(PROPS_TEXTURES / f'{source}_{kind}.png', HERE / 'textures' / f'{name}_{kind}.png')
    print('TEXTURE', name, (srgb.reshape(-1, 3).mean(0) * 255).round())


def tileable_noise(size, cells, rng):
    """Smooth periodic value noise: a random grid upsampled with wrap-around cubic blending."""
    grid = rng.random((cells, cells))
    t = np.arange(size) * cells / size
    i = np.floor(t).astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    rows = grid[i % cells] * (1 - f)[:, None] + grid[(i + 1) % cells] * f[:, None]
    return rows[:, i % cells] * (1 - f)[None, :] + rows[:, (i + 1) % cells] * f[None, :]


def wax():
    rng = np.random.default_rng(11)
    size = 128
    shade = 0.6 * tileable_noise(size, 8, rng) + 0.4 * tileable_noise(size, 32, rng)
    # Drips: stretched noise along v (rows), lighter streaks running down the candle.
    drips = tileable_noise(size, 16, rng)[:, :1].repeat(size, 1).T
    value = 0.975 + 0.03 * (shade - 0.5) + 0.03 * (drips - 0.5)
    colour = np.stack([value * 1.0, value * 0.975, value * 0.91], -1)
    Image.fromarray((np.clip(colour, 0, 1) * 255).astype(np.uint8), 'RGB').save(HERE / 'textures' /
                                                                                 'wax_basecolor.png', optimize=True)
    print('TEXTURE wax', colour.reshape(-1, 3).mean(0) * 255)


if __name__ == '__main__':
    wax()
    brighten('bone', 'bonelight')
    brighten('skull', 'skulllight')
