#!/usr/bin/env python3
"""XD-04's textures that are cut or built from finished ones (no generation of their own): python3 xd04_derive.py

- xwface1-4: the Rosebud door's four quarters (top-left, top-right, bottom-left, bottom-right), 256 x 256 each. The
  door is 320 x 320 and its two folding leaves lay the quarters at their own size meeting in the middle, so each
  quarter shows its inner 160 x 160: the finished face (finished/xwface.png) fills the middle 320 x 320 of a 512 x 512
  picture, the never-seen rim mirrored round it.
- xwward: the ward's picture made at the leaf's own 192 x 320 (finished/xwward.png, written by xtex.py finish) padded
  to 256 x 512 by mirroring (the leaf shows the top-left 192 x 320 from the sanctum, the mirrored rim from behind).
  Run once after finish: a padded file is left alone.
- xwcage: the cage bars, 128 x 256, cut from the riveted iron (finished/xwiron.png): four round bars every 32 units,
  straps at the top, middle and foot, rivets where they cross; everything else transparent (the colour of the nearest
  iron kept under the alpha, so mipmaps carry no stray colour).
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FIN = HERE / 'finished'
S = 4


def save(image, name):
    image.save(FIN / f'{name}.png')
    w, h = image.size
    image.resize((w // 2, h // 2), Image.LANCZOS).save(FIN / f'{name}_x2.png')
    image.resize((w // 4, h // 4), Image.LANCZOS).save(FIN / f'{name}_x1.png')
    print(name, image.size)


def face_quarters():
    face = Image.open(FIN / 'xwface.png').convert('RGB').resize((320 * S, 320 * S), Image.LANCZOS)
    rim = (512 - 320) // 2 * S
    canvas = np.pad(np.asarray(face), ((rim, rim), (rim, rim), (0, 0)), mode='reflect')
    half = 256 * S
    for number, (y, x) in enumerate(((0, 0), (0, half), (half, 0), (half, half)), 1):
        save(Image.fromarray(np.ascontiguousarray(canvas[y:y + half, x:x + half])), f'xwface{number}')


def ward_pad():
    ward = Image.open(FIN / 'xwward.png').convert('RGBA')
    if ward.size == (256 * S, 512 * S):
        print('xwward already padded')
        return
    assert ward.size == (192 * S, 320 * S), ward.size
    rgba = np.asarray(ward)
    padded = np.pad(rgba, ((0, (512 - 320) * S), (0, (256 - 192) * S), (0, 0)), mode='reflect')
    save(Image.fromarray(np.ascontiguousarray(padded), 'RGBA'), 'xwward')


def cage_bars():
    iron = np.asarray(Image.open(FIN / 'xwiron.png').convert('RGB'), float)
    width, height = 128 * S, 256 * S
    tiled = np.tile(iron, (height // iron.shape[0] + 1, width // iron.shape[1] + 1, 1))[:height, :width]
    x = np.arange(width)[None, :].repeat(height, 0)
    y = np.arange(height)[:, None].repeat(width, 1)
    opaque = np.zeros((height, width), bool)
    shade = np.ones((height, width))
    # Round vertical bars, 10 units thick, centred every 32 units (16, 48, 80, 112): the repeat is seamless.
    bar_half = 5 * S
    for centre in range(16 * S, width, 32 * S):
        d = np.abs(x - centre)
        on = d <= bar_half
        opaque |= on
        shade = np.where(on, 0.55 + 0.6 * np.cos(np.clip(d / bar_half, 0, 1) * np.pi / 2), shade)
    # Flat riveted straps across: at the top, the middle and the foot (12 units high).
    for top in (0, 122 * S, 244 * S):
        on = (y >= top) & (y < top + 12 * S)
        opaque |= on
        edge = np.minimum(y - top, top + 12 * S - 1 - y) / (2 * S)
        shade = np.where(on, np.clip(0.75 + 0.25 * np.clip(edge, 0, 1), 0, 1.1), shade)
        # Rivets where the straps cross the bars.
        for centre in range(16 * S, width, 32 * S):
            r = np.hypot(x - centre, y - (top + 6 * S))
            rivet = r <= 3.5 * S
            shade = np.where(rivet, 1.0 + 0.5 * np.cos(np.clip(r / (3.5 * S), 0, 1) * np.pi / 2), shade)
    rgb = np.clip(tiled * shade[..., None], 0, 255)
    _, (iy, ix) = ndimage.distance_transform_edt(~opaque, return_indices=True)
    rgb = rgb[iy, ix]
    alpha = (opaque * 255).astype(np.uint8)
    save(Image.fromarray(np.dstack([rgb.astype(np.uint8), alpha]), 'RGBA'), 'xwcage')


if __name__ == '__main__':
    face_quarters()
    ward_pad()
    if (FIN / 'xwiron.png').exists():
        cage_bars()
