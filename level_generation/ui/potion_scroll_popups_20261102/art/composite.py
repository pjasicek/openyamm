#!/usr/bin/env python3
"""Puts a socketed end ornament into the native basebar capture for the mockup.

The capture (../../maw_potion_radial_20261025/gameplay_backdrop.jpg, 1600x900, five members) draws the compact
ornament as GameplayUiSkin::renderPartyBasebar does: its registered region [330, 103, 722, 1429] of the 992x1585 sprite
at x 338.0-395.2 (left; the right one mirrored at 1204.9-1262.1) and y 705-900. This script removes that ornament
(its own alpha, filled with the blurred grass beside it) and draws the new one with its rail's right edge and its
height in the same place, so it attaches to the frame as the engine would draw it.

    python3 composite.py endcap_socket_v1.png ../previews/backdrop_v1.jpg

Prints the socket centre and radius on screen (left and right) for the page.
"""
import sys

import numpy as np
from PIL import Image

HERE = __file__.rsplit('/', 1)[0]
BACKDROP = f'{HERE}/../../maw_potion_radial_20261025/gameplay_backdrop.jpg'
OLD = f'{HERE}/source_endcap_compact.png'
OLD_BOX = (330, 103, 722, 1429)
TOP, BOTTOM = 705.0, 900.0
LEFT_X0, LEFT_X1 = 338.0, 395.2
RIGHT_X0 = 1204.9


def bbox(alpha, threshold=24):
    ys, xs = np.nonzero(alpha > threshold)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def remove_old(scene):
    old = Image.open(OLD).convert('RGBA').crop(OLD_BOX)
    width = round(LEFT_X1 - LEFT_X0)
    height = round(BOTTOM - TOP)
    mask = np.array(old.resize((width, height), Image.LANCZOS))[:, :, 3] > 8
    pixels = np.array(scene)
    for x0, mirrored, shift in ((round(LEFT_X0), False, -72), (round(RIGHT_X0), True, 72)):
        m = mask[:, ::-1] if mirrored else mask
        # Grow the mask a little so no brass fringe stays behind.
        grown = m.copy()
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                grown |= np.roll(np.roll(m, dy, 0), dx, 1)
        for y in range(height):
            for x in range(width):
                if grown[y, x]:
                    sx, sy = x0 + x, round(TOP) + y
                    # Keep the frame itself (the rail overlaps it; the new ornament redraws the rail).
                    if (not mirrored and sx >= 383) or (mirrored and sx <= 1217):
                        continue
                    pixels[sy, sx] = pixels[sy, sx + shift]
    return Image.fromarray(pixels)


def socket(art):
    """The socket: the largest dark, opaque, roughly round blob inside the ornament."""
    a = np.array(art).astype(int)
    dark = (a[:, :, 3] > 200) & (a[:, :, :3].max(axis=2) < 80)
    from scipy import ndimage
    labels, count = ndimage.label(dark)
    best = None
    for index in range(1, count + 1):
        ys, xs = np.nonzero(labels == index)
        w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        fill = len(xs) / (w * h)
        if 0.6 < w / h < 1.6 and fill > 0.6 and (best is None or len(xs) > best[0]):
            best = (len(xs), (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (w + h) / 4)
    return best[1:]


def main():
    source, out = sys.argv[1], sys.argv[2]
    art = Image.open(source).convert('RGBA')
    x0, y0, x1, y1 = bbox(np.array(art)[:, :, 3])
    art = art.crop((x0, y0, x1, y1))
    scale = (BOTTOM - TOP) / art.height
    width = round(art.width * scale)
    sprite = art.resize((width, round(BOTTOM - TOP)), Image.LANCZOS)
    scene = remove_old(Image.open(BACKDROP).convert('RGB')).convert('RGBA')
    left = round(LEFT_X1) - width
    scene.alpha_composite(sprite, (left, round(TOP)))
    scene.alpha_composite(sprite.transpose(Image.FLIP_LEFT_RIGHT), (round(RIGHT_X0), round(TOP)))
    scene.convert('RGB').save(out, quality=92)
    cx, cy, r = socket(art)
    print(f'left {left + cx * scale:.1f} {TOP + cy * scale:.1f} r {r * scale:.1f}')
    print(f'right {RIGHT_X0 + width - cx * scale:.1f} {TOP + cy * scale:.1f} r {r * scale:.1f}')
    print(f'ornament width {width}px (was {LEFT_X1 - LEFT_X0:.0f})')


if __name__ == '__main__':
    main()
