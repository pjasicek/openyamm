#!/usr/bin/env python3
"""Texture sets of the Xeen engine props, written to textures/<name>_{basecolor,normal,mr}.png (mr: G roughness,
B metal; normal OpenGL tangent space):
- hay: tileable loose straw (1024, one repeat per 1.2 m): golden stalks in several layers over dark straw shadow.
- haystrand: RGBA atlas of four loose straw tufts (2 x 2, roots at each cell's bottom edge) for the alpha-tested
  fringe cards; colour dilated into the transparent texels against mip fringes.
- driftwood: Poly Haven rough_wood (CC0, ../mm6_new_sorpigal_3d/trees/source/rough_wood, read only), 1024,
  pushed toward the sprite's silver-grey with a faint pink-brown cast.
- bottle: the bottle's cylindrical unwrap (512; u around, v = height / bottle height): olive glass, the yellow label
  band on the front half, the pale lip ring and the cork; the cork top and the bottom cap map into its corners.
Usage: make_textures.py [name ...]"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'textures')
ROUGH_WOOD = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'trees', 'source',
                          'rough_wood')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(4711)

# Bottle profile (shared with build_bottle.py): (radius, z) in sprite x2 pixels, bottom to top; height 123.
BOTTLE_HEIGHT = 123.0
BOTTLE_LABEL = (15.0, 29.0)        # label band, z range
BOTTLE_LIP = (104.0, 110.0)        # pale lip ring
BOTTLE_CORK = 110.0                # cork from here to the top


def noise(shape, beta=2.0, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1]."""
    field = rng.normal(size=shape)
    fy = np.fft.fftfreq(shape[0])[:, None] * scale[0]
    fx = np.fft.fftfreq(shape[1])[None, :] * scale[1]
    radius = np.sqrt(fx * fx + fy * fy); radius[0, 0] = 1.0
    spectrum = np.fft.fft2(field) / radius ** beta; spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifft2(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def mix(t, a, b):
    t = np.clip(t, 0, 1)[..., None]
    return linear(a) * (1 - t) + linear(b) * t


def normal_from_height(height, strength, wrap=True):
    mode = 'wrap' if wrap else 'nearest'
    dx = ndimage.correlate1d(height, [-0.5, 0, 0.5], axis=1, mode=mode) * strength
    dy = ndimage.correlate1d(height, [-0.5, 0, 0.5], axis=0, mode=mode) * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save_rgb(name, kind, array):
    Image.fromarray((np.clip(array, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_{kind}.png'))


def save_mr(name, rough, metal=0.0):
    rough = np.asarray(rough, np.float64)
    mr = np.dstack([np.zeros(rough.shape), rough, np.full(rough.shape, metal)])
    save_rgb(name, 'mr', mr)


def report(name, colour_srgb, alpha=None):
    px = colour_srgb.reshape(-1, 3) if alpha is None else colour_srgb[alpha > 0.5]
    print('TEXTURE', name, colour_srgb.shape[:2], 'mean sRGB', (px.mean(0) * 255).round(1))


def strokes(size, count, length, width, angle, tones, curl=0.0, wrap=True):
    """Height and tone fields of random straight or slightly bent stalks (wrap-around when wrap)."""
    tiles = 3 if wrap else 1
    height = Image.new('L', (size * tiles, size * tiles), 0)
    tone = Image.new('L', (size * tiles, size * tiles), 0)
    dh, dt = ImageDraw.Draw(height), ImageDraw.Draw(tone)
    for _ in range(count):
        x, y = rng.uniform(0, size, 2)
        a = rng.uniform(*angle)
        n = rng.uniform(*length)
        w = int(rng.integers(width[0], width[1] + 1))
        bend = rng.normal(0, curl)
        pts = []
        for k in range(4):
            t = k / 3
            aa = a + bend * t
            pts.append((x + np.cos(aa) * n * t, y + np.sin(aa) * n * t))
        level = int(rng.uniform(150, 255)); shade = int(rng.uniform(*tones))
        offsets = (0, size, 2 * size) if wrap else (0,)
        for ox in offsets:
            for oy in offsets:
                p = [(px + ox, py + oy) for px, py in pts]
                dh.line(p, fill=level, width=w); dt.line(p, fill=shade, width=w)
    crop = (size, size, 2 * size, 2 * size) if wrap else (0, 0, size, size)
    return (np.asarray(height.crop(crop), np.float64) / 255.0, np.asarray(tone.crop(crop), np.float64) / 255.0)


def hay():
    """Coarse loose straw: one repeat per 1.2 m (TILE in build_hay.py), stalks 8-28 map units long and about one
    wide (the sprite's), three layers over deep brown gaps, each layer shadowing the ones below."""
    n = 1024
    colour = mix(noise((n, n), 2.2), (40, 24, 8), (78, 50, 20))
    height = noise((n, n), 1.0) * 0.1
    layers = [(1300, (70, 200), (4, 7), (40, 170), (104, 64, 22), (196, 140, 66), 0.35),
              (1000, (90, 250), (4, 8), (80, 220), (150, 100, 40), (236, 186, 104), 0.6),
              (520, (110, 290), (5, 8), (140, 255), (190, 140, 66), (252, 226, 150), 0.85)]
    for count, length, width, tones, dark, light, top in layers:
        h, t = strokes(n, count, length, width, (-np.pi, np.pi), tones, curl=0.2)
        mask = (h > 0.05)[..., None]
        core = ndimage.gaussian_filter(h, 1.5, mode='wrap') / np.maximum(h, 1e-3)
        shade = 0.55 + 0.45 * np.clip(core, 0, 1) ** 1.5             # rounded stalks: dark edges, bright core
        col = mix(t, dark, light) * shade[..., None]
        colour = np.where(mask, col, colour * 0.7)          # each new layer shadows what lies under it
        height = np.where(h > 0.05, top + 0.15 * h * np.clip(core, 0, 1), height)
    colour = srgb(colour)
    save_rgb('hay', 'basecolor', colour)
    save_rgb('hay', 'normal', normal_from_height(ndimage.gaussian_filter(height, 1.0, mode='wrap'), 8.0))
    save_mr('hay', 0.9 - 0.1 * height)
    report('hay', colour)


def haystrand():
    n, cell = 512, 256
    rgba = np.zeros((n, n, 4))
    for cy in range(2):
        for cx in range(2):
            img = Image.new('RGBA', (cell, cell), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            count = int(rng.integers(30, 44))
            for _ in range(count):
                root = (cell / 2 + rng.normal(0, cell * 0.12), cell - 2)
                a = -np.pi / 2 + rng.normal(0, 0.55)
                length = rng.uniform(0.45, 0.97) * cell
                bend = rng.normal(0, 0.35)
                pts = []
                for k in range(6):
                    t = k / 5
                    aa = a + bend * t * t
                    pts.append((root[0] + np.cos(aa) * length * t * 0.9, root[1] + np.sin(aa) * length * t))
                tone = rng.uniform(0, 1)
                c = srgb(mix(np.array(tone), (150, 108, 50), (246, 216, 140))) * 255
                d.line(pts, fill=(int(c[0]), int(c[1]), int(c[2]), 255), width=int(rng.integers(3, 6)))
            a = np.asarray(img, np.float64) / 255.0
            rgba[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell] = a
    alpha = rgba[..., 3]
    colour = rgba[..., :3]
    # dilate the stalk colour into the transparent texels (mip and filtering fringes take stalk colour, not black)
    weight = ndimage.gaussian_filter(alpha, 6)
    fill = np.dstack([ndimage.gaussian_filter(colour[..., i] * alpha, 6) for i in range(3)]) / np.maximum(
        weight, 1e-4)[..., None]
    mean = colour[alpha > 0.5].mean(0)
    fill = np.where((weight > 1e-3)[..., None], fill, mean)
    colour = np.where((alpha > 0.5)[..., None], colour, fill)
    out = np.dstack([colour, alpha])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(
        os.path.join(OUT, 'haystrand_basecolor.png'))
    save_mr('haystrand', np.full(alpha.shape, 0.9))
    report('haystrand', colour, alpha)


def driftwood():
    n = 1024
    diff = np.asarray(Image.open(os.path.join(ROUGH_WOOD, 'rough_wood_diff_2k.png')).convert('RGB').resize(
        (n, n), Image.LANCZOS), np.float64) / 255.0
    lum = diff @ np.array([0.2126, 0.7152, 0.0722])
    lum = lum / lum.mean()
    # silver-grey wood with a faint pink-brown cast in the darker grain (the sprite's driftwood)
    grey = np.array([0.62, 0.60, 0.57]); warm = np.array([0.50, 0.40, 0.34])
    w = np.clip(1.2 - lum, 0, 1)[..., None]
    colour = np.clip(lum[..., None] ** 1.7 * (grey * (1 - w) + warm * w), 0, 1)
    save_rgb('driftwood', 'basecolor', colour)
    nor = Image.open(os.path.join(ROUGH_WOOD, 'rough_wood_nor_gl_2k.png')).convert('RGB').resize((n, n), Image.LANCZOS)
    nor.save(os.path.join(OUT, 'driftwood_normal.png'))
    rough = np.asarray(Image.open(os.path.join(ROUGH_WOOD, 'rough_wood_rough_2k.png')).convert('L').resize(
        (512, 512), Image.LANCZOS), np.float64) / 255.0
    save_mr('driftwood', 0.72 + 0.23 * rough)
    report('driftwood', colour)


def bottle():
    n = 512
    v = (np.arange(n)[::-1] + 0.5) / n                   # image row -> v (0 bottom)
    z = np.repeat((v * BOTTLE_HEIGHT)[:, None], n, 1)
    uu = np.repeat(((np.arange(n) + 0.5) / n)[None, :], n, 0)
    glass_t = noise((n, n), 1.8) * 0.45 + noise((n, n), 1.0, scale=(1.0, 6.0)) * 0.25 + noise((n, n), 0.5) * 0.3
    colour = mix(glass_t, (104, 108, 58), (196, 194, 122))
    colour *= (0.82 + 0.36 * noise((n, n), 0.2))[..., None]          # fine sparkle, as the sprite's glass
    rough = np.full((n, n), 0.18)
    # pale lip ring
    lip = (z >= BOTTLE_LIP[0]) & (z < BOTTLE_LIP[1])
    colour = np.where(lip[..., None], mix(glass_t, (140, 142, 96), (196, 196, 146)), colour)
    # cork
    cork = z >= BOTTLE_CORK
    cork_t = noise((n, n), 1.2) * 0.7 + noise((n, n), 0.6) * 0.3
    colour = np.where(cork[..., None], mix(cork_t, (78, 50, 22), (140, 98, 52)), colour)
    rough = np.where(cork, 0.85, rough)
    # label: the front half (u 0.63..0.87, centred on -y), yellow paper with orange smudges and darker torn edges
    lab = (z >= BOTTLE_LABEL[0]) & (z < BOTTLE_LABEL[1]) & (uu > 0.63) & (uu < 0.87)
    smudge = noise((n, n), 2.0)
    edge = np.minimum.reduce([z - BOTTLE_LABEL[0], BOTTLE_LABEL[1] - z, (uu - 0.63) * 360, (0.87 - uu) * 360])
    label = mix(smudge, (214, 168, 30), (246, 214, 70)) * (0.75 + 0.25 * np.clip(edge / 1.5, 0, 1))[..., None]
    colour = np.where(lab[..., None], label, colour)
    rough = np.where(lab, 0.8, rough)
    colour = srgb(colour)
    save_rgb('bottle', 'basecolor', colour)
    height = np.where(lab, 0.3, 0.0) + np.where(cork, cork_t * 0.5, 0.0)
    save_rgb('bottle', 'normal', normal_from_height(height, 2.0, wrap=False))
    save_mr('bottle', rough)
    report('bottle', colour)


if __name__ == '__main__':
    names = sys.argv[1:] or ['hay', 'haystrand', 'driftwood', 'bottle']
    for name in names:
        globals()[name]()
