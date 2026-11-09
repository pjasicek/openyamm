#!/usr/bin/env python3
"""Textures for the crystal batch (textures/): procedural, tileable maps built from FFT-filtered noise, plus the Memory
Crystal ball flipbook cut from the six restored native frames.
- crystal: near-white, faintly clouded crystal with streaks along texture v (the prism length); glossy dielectric
  (roughness 0.12-0.18); the native colour ramps come through COLOR_0.
- dripstone: rugged limestone for the stalagmites: terraced blocks across texture v (the height) with painted top
  light (bright ledge tops, dark undersides, as the sprite), ochre and umber mottling, pale calcite drips; matte.
- dishmetal: smooth dark metal for the Memory Crystal's cradle (dielectric gloss; the tint gives the grey).
- greyrock: speckled grey rock for the crys6 mound (granite-like, lighter than the props granite).
- memball: the native ball (mcryst01-06, x2 frames) as a 3 x 2 flipbook atlas, transparent outside the ball; colour
  bleeds into the transparent texels so mip levels keep no dark fringe.
Each procedural map: <name>_basecolor.png (sRGB), <name>_normal.png (OpenGL), <name>_mr.png (G rough, B metal).
Usage: make_textures.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
X2 = REPO / 'assets_dev/engine/decorations_x2'
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(4913)
SIZE = 512
MEMBALL_COLUMNS, MEMBALL_ROWS = 3, 2
MEMBALL_BOX = (1, 4, 87, 90)          # the ball in the 88 x 130 x2 frames (left, top, right, bottom)


def noise(shape, beta=2.0, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1]; scale multiplies the (row, column) frequencies (large = stretched along that axis)."""
    field = rng.normal(size=shape)
    fy, fx = np.meshgrid(np.fft.fftfreq(shape[0]) * scale[0], np.fft.fftfreq(shape[1]) * scale[1], indexing='ij')
    radius = np.sqrt(fy * fy + fx * fx)
    radius[0, 0] = 1.0
    spectrum = np.fft.fft2(field) / radius ** beta
    spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifft2(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, colour_linear, height, strength, roughness, metal):
    rgb = (srgb(colour_linear) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(rgb).save(OUT / f'{name}_basecolor.png', optimize=True)
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        OUT / f'{name}_normal.png', optimize=True)
    rough = np.broadcast_to(np.asarray(roughness, np.float64), height.shape)
    mr = np.dstack([np.zeros(height.shape), rough, np.full(height.shape, metal)])
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_mr.png', optimize=True)
    linear_mean = np.clip(colour_linear, 0, 1).reshape(-1, 3).mean(0)
    print('TEXTURE', name, 'mean sRGB', (srgb(colour_linear).reshape(-1, 3).mean(0) * 255).round(1),
          'mean linear', linear_mean.round(4))
    return linear_mean.tolist()


def crystal():
    shape = (SIZE, SIZE)
    cloud = noise(shape, 2.2)
    streak = noise(shape, 1.6, scale=(6.0, 0.35))       # long along v (rows), narrow across u
    fine = noise(shape, 1.0)
    value = 0.8 + 0.12 * cloud + 0.1 * streak - 0.04 * fine
    colour = np.dstack([value, value, value])
    height = 0.6 * streak + 0.4 * cloud
    rough = 0.12 + 0.06 * fine
    return save('crystal', colour, height, 1.5, rough, 0.0)


def dripstone():
    shape = (SIZE, SIZE)
    # Terraced height field: broad blocks stretched across texture u, quantised into ledges.
    field = 0.6 * noise(shape, 1.6, scale=(1.0, 3.0)) + 0.4 * noise(shape, 1.2, scale=(1.0, 1.5))
    terraces = np.floor(field * 9) / 9 * 0.75 + field * 0.25
    # Painted top light as on the sprite: ledge tops (height falling toward texture row + 3) bright, undersides dark.
    emboss = terraces - np.roll(terraces, 3, axis=0)
    shade = np.clip(1.0 + 12.0 * emboss, 0.08, 2.0)
    drips = noise(shape, 1.05, scale=(7.0, 0.5))
    drips = np.clip(0.5 + (drips - ndimage.uniform_filter(drips, 64, mode='wrap')) * 1.6, 0, 1)   # no broad bands
    mottle = noise(shape, 1.7)
    grain = noise(shape, 0.8)
    ochre = np.array([0.40, 0.27, 0.16])
    umber = np.array([0.21, 0.19, 0.18])
    calcite = np.array([0.82, 0.76, 0.68])
    m = mottle[..., None]
    colour = (ochre[None, None] * m + umber[None, None] * (1 - m)) * (0.7 + 0.6 * grain[..., None])
    white = np.clip((drips - 0.5) * 2.5, 0, 1) * np.clip(shade - 0.5, 0, 1)
    colour = colour * (1 - white[..., None]) + calcite[None, None] * white[..., None]
    colour = colour * shade[..., None]
    height = terraces + 0.15 * drips + 0.05 * grain
    return save('dripstone', colour, height, 9.0, 0.88, 0.0)


def dishmetal():
    shape = (SIZE, SIZE)
    smear = noise(shape, 1.5, scale=(0.4, 4.0))
    fine = noise(shape, 1.0)
    value = 0.42 + 0.14 * smear + 0.04 * fine
    colour = np.dstack([value, value, value * 1.03])
    return save('dishmetal', colour, 0.7 * smear + 0.3 * fine, 0.8, 0.12 + 0.06 * fine, 0.0)


def greyrock():
    shape = (SIZE, SIZE)
    grain = noise(shape, 1.2)
    blotch = noise(shape, 2.0)
    speck = np.clip((noise(shape, 0.6) - 0.62) * 5.0, 0, 1)
    value = 0.32 + 0.3 * blotch + 0.18 * grain - 0.22 * speck
    colour = np.dstack([value * 1.0, value * 1.0, value * 0.97])
    return save('greyrock', colour, 0.5 * blotch + 0.5 * grain - 0.3 * speck, 4.0, 0.85, 0.0)


def memball():
    files = {b['name'].lower(): b['file'] for b in json.loads((X2 / 'manifest.json').read_text())['bindings']}
    left, top, right, bottom = MEMBALL_BOX
    width, height = right - left, bottom - top
    atlas = Image.new('RGBA', (width * MEMBALL_COLUMNS, height * MEMBALL_ROWS), (0, 0, 0, 0))
    for index in range(MEMBALL_COLUMNS * MEMBALL_ROWS):
        cell = np.asarray(Image.open(X2 / files[f'mcryst{index + 1:02d}']).convert('RGBA').crop(MEMBALL_BOX)).copy()
        alpha = cell[..., 3] > 128
        # Bleed the edge colour outward into the transparent texels (nearest opaque texel).
        _, (iy, ix) = ndimage.distance_transform_edt(~alpha, return_indices=True)
        cell[..., :3] = cell[iy, ix, :3]
        cell[..., 3] = np.where(alpha, 255, 0)
        atlas.paste(Image.fromarray(cell), ((index % MEMBALL_COLUMNS) * width, (index // MEMBALL_COLUMNS) * height))
    atlas.save(OUT / 'memball_basecolor.png', optimize=True)
    print('FLIPBOOK memball', atlas.size, f'{MEMBALL_COLUMNS}x{MEMBALL_ROWS}')


def main():
    means = {'crystal': crystal(), 'dripstone': dripstone(), 'dishmetal': dishmetal(), 'greyrock': greyrock()}
    memball()
    (OUT / 'means.json').write_text(json.dumps(means, indent=1) + '\n')


if __name__ == '__main__':
    main()
