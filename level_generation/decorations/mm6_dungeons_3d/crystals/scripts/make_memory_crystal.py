#!/usr/bin/env python3
"""Textures of the Memory Crystal `mcryst01`, revision 2 (crystals/textures/):

- memorb_basecolor.png: the ball's 3 x 2 flipbook. The six restored frames are not played (their upscaling
  differs frame to frame). Every frame holds one still ball: the per-texel median of the six restored ball frames
  (the sparkles move, so the median keeps only the ghostly face and the dark glass), with a painted glass highlight
  and rim. The animation is drawn on top: crisp pink-white sparkles (and the red eye glints) at the positions,
  sizes and colours measured in the six native 44 x 65 frames (assets_dev/_legacy/sprites_original/mcrystNN.bmp).
  Transparent outside the ball; colour bled outward so mip levels keep no dark fringe.
- memdisc_{basecolor,normal,mr}.png: the stand disc's scratched dark metal from CC0 Poly Haven `blue_metal_plate`
  (textures/polyhaven/): luminance only (the colour comes from the sprite's ramp in COLOR_0), its normal map
  softened, its roughness remapped to a polished range (G roughness, B metal 0: dielectric gloss, see README).
Usage: make_memory_crystal.py"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
X2 = REPO / 'assets_dev/engine/decorations_x2'
NATIVE = REPO / 'assets_dev/_legacy/sprites_original'
OUT = HERE / 'textures'
POLYHAVEN = OUT / 'polyhaven'
COLUMNS, ROWS = 3, 2
BOX_X2 = (1, 4, 87, 90)          # the ball in the 88 x 130 restored frames (left, top, right, bottom)
CELL = 128                       # texels per flipbook frame (the restored ball is 86 across)
LUMA = np.array([0.2126, 0.7152, 0.0722])


def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def native_frames():
    frames = []
    for index in range(1, 7):
        image = Image.open(NATIVE / f'mcryst{index:02d}.bmp')
        palette = np.array(image.getpalette()).reshape(-1, 3)
        frames.append(palette[np.asarray(image)].astype(np.float64))
    return np.array(frames)


def sparkles(frames):
    """Per frame: (x, y, radius, colour) in native pixels of the sparkles and eye glints (pink, brighter than the
    median of the six frames), from connected blobs of at least four texels."""
    median = np.median(frames, 0)
    found = []
    for frame in frames:
        redness = frame[..., 0] - (frame[..., 1] + frame[..., 2]) / 2
        mask = (redness > 20) & (frame.mean(-1) - median.mean(-1) > 8)
        mask[43:] = False                                  # the ball only
        labels, count = ndimage.label(ndimage.binary_dilation(mask, iterations=1) & (frame.mean(-1) > 60))
        blobs = []
        for k in range(1, count + 1):
            ys, xs = np.where((labels == k) & mask)
            if len(xs) < 4:
                continue
            peak = frame[ys, xs][np.argmax(frame[ys, xs].sum(-1))]
            blobs.append((xs.mean(), ys.mean(), np.sqrt(len(xs) / np.pi), peak / 255))
        found.append(blobs)
    return found


def ball_still():
    """Median of the six restored ball frames (RGBA, CELL x CELL)."""
    cells = []
    for index in range(1, 7):
        image = Image.open(X2 / f'mcryst{index:02d}_p549.png').convert('RGBA').crop(BOX_X2)
        cells.append(np.asarray(image.resize((CELL, CELL), Image.LANCZOS), np.float64) / 255)
    cells = np.array(cells)
    still = np.median(cells, 0)
    return still


def glass(still):
    """Painted glass: a soft highlight upper left, a faint lavender rim light lower right, the edge darkened."""
    y, x = (np.mgrid[0:CELL, 0:CELL] + 0.5) / CELL * 2 - 1
    y = -y
    r = np.sqrt(x * x + y * y)
    lin = linear(still[..., :3])
    edge = np.clip((r - 0.78) / 0.22, 0, 1) ** 1.5
    lin *= (1 - 0.45 * edge)[..., None]
    highlight = np.exp(-((x + 0.42) ** 2 + (y - 0.5) ** 2) / 0.006) * 0.35
    highlight += np.exp(-((x + 0.3) ** 2 + (y - 0.55) ** 2) / 0.08) * 0.03
    lower_right = np.clip(0.5 * (x - y), 0, 1)
    rim = np.exp(-((r - 0.86) / 0.06) ** 2) * lower_right * 0.12
    lin += highlight[..., None] * np.array([0.9, 0.88, 1.0]) + rim[..., None] * np.array([0.55, 0.45, 0.8])
    out = still.copy()
    out[..., :3] = srgb(lin)
    out[..., 3] = (r < 0.985).astype(np.float64)        # a clean round outline (the restored alpha is stepped)
    return out


def draw_sparkles(cell, blobs):
    """Additive glows in linear light: a white-pink core, a pink halo and a faint four-point star."""
    scale = CELL / 43.0                                  # native ball pixels (cols 1..42, rows 0..42) to texels
    y, x = np.mgrid[0:CELL, 0:CELL] + 0.5
    lin = linear(cell[..., :3])
    for bx, by, radius, colour in blobs:
        cx, cy = (bx - 0.5) * scale, (by + 0.5) * scale
        d2 = ((x - cx) ** 2 + (y - cy) ** 2) / (scale * scale)
        size = min(2.2, max(0.9, radius * 0.6))
        core = np.exp(-d2 / (0.3 * size * size))
        halo = np.exp(-d2 / (1.6 * size * size)) * 0.3
        star = (np.exp(-((x - cx) / scale) ** 2 / 0.05) * np.exp(-((y - cy) / scale) ** 2 / (1.4 * size * size))
                + np.exp(-((y - cy) / scale) ** 2 / 0.05) * np.exp(-((x - cx) / scale) ** 2 / (1.4 * size * size)))
        tint = linear(np.clip(colour, 0, 1))
        pink = linear(np.array([0.93, 0.55, 0.72]))
        lin += core[..., None] * (0.6 * tint + 0.4) + (halo + 0.12 * star)[..., None] * pink
    out = cell.copy()
    out[..., :3] = srgb(lin)
    return out


def bleed(cell):
    alpha = cell[..., 3] > 0.5
    _, (iy, ix) = ndimage.distance_transform_edt(~alpha, return_indices=True)
    out = cell.copy()
    out[..., :3] = cell[iy, ix, :3]
    out[..., 3] = alpha.astype(np.float64)
    return out


def memorb():
    frames = native_frames()
    blobs = sparkles(frames)
    still = glass(ball_still())
    atlas = np.zeros((CELL * ROWS, CELL * COLUMNS, 4))
    for index in range(COLUMNS * ROWS):
        cell = bleed(draw_sparkles(still, blobs[index]))
        r, c = divmod(index, COLUMNS)
        atlas[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = cell
        print('FRAME', index + 1, [(round(b[0], 1), round(b[1], 1), round(b[2], 2)) for b in blobs[index]])
    path = OUT / 'memorb_basecolor.png'
    Image.fromarray((np.clip(atlas, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)
    path.chmod(0o664)
    print('WROTE', path, atlas.shape)


def memdisc(size=512):
    diff = np.asarray(Image.open(POLYHAVEN / 'blue_metal_plate_diff_1k.png').convert('RGB'), np.float64) / 255
    nrm = np.asarray(Image.open(POLYHAVEN / 'blue_metal_plate_nor_gl_1k.png').convert('RGB'), np.float64) / 255
    rough = np.asarray(Image.open(POLYHAVEN / 'blue_metal_plate_rough_1k.png'), np.float64) / 255
    lum = linear(diff) @ LUMA
    lum = lum / lum.mean()
    grey = srgb(np.clip(0.5 * (1 + (lum - 1) * 0.6), 0, 1))           # neutral mid grey with the plate's wear
    n = nrm * 2 - 1
    n[..., :2] *= 0.5
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rn = (rough - rough.mean()) / (rough.std() + 1e-9)
    gloss = np.clip(0.32 + 0.08 * rn, 0.18, 0.5)
    maps = {'basecolor': np.repeat(grey[..., None], 3, -1), 'normal': n * 0.5 + 0.5,
            'mr': np.stack([np.ones_like(gloss), gloss, np.zeros_like(gloss)], -1)}
    for name, data in maps.items():
        image = Image.fromarray((np.clip(data, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((size, size),
                                                                                         Image.LANCZOS)
        path = OUT / f'memdisc_{name}.png'
        image.save(path, optimize=True)
        path.chmod(0o664)
        print('WROTE', path)


if __name__ == '__main__':
    memorb()
    memdisc()
