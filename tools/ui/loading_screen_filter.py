#!/usr/bin/env python3
"""Give AI-generated loading screens the hand-made late-90s feel of MM6-MM8's own loading screens.

The Xeen loading screens (worlds/xeen/icons_x2/xeenload{c,d}{1,2}.png) were generated images: too-clean gradients,
plastic micro-detail, uniform sharpness and bright, saturated colour. MM6-MM8's screens (engine/icons_x2/7load*.png,
loading*.png) are pre-rendered or painted art shown in 16-bit colour: firm outlines, flat painted planes, deep
shadows, warm and slightly muted colour, and the faint texture of 16-bit dithering.

This script applies a stack of subtle passes, each with its parameters in VARIANTS below:

  paint      edge-aware Kuwahara smoothing (flattens plastic micro-detail into painted planes, keeps outlines)
  grade      desaturate the loudest colours, warm the image, deepen shadows with an S-curve
  edges      a light unsharp mask on the painted result so outlines stay firm
  canvas     a faint woven canvas/paper texture
  grain      fine monochrome grain, strongest in the midtones
  dither     16-bit colour (RGB555) with an ordered 4x4 Bayer dither at the era's 640x480 working size
  chroma     a one-pixel radial colour fringe (aged print)
  vignette   soft darkening toward the corners

The loading bar frame baked into the bottom of each image is protected: it receives only the colour grade.

Usage (always from the untouched originals, never from installed results):
  python3 tools/ui/loading_screen_filter.py --src output/xeen_loading_filter/originals \
      --out output/xeen_loading_filter/variants            # every variant, for comparison
  python3 tools/ui/loading_screen_filter.py --src output/xeen_loading_filter/originals \
      --variant combined --install assets_dev/worlds/xeen/icons_x2   # install the chosen variant in place
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

IMAGES = ['xeenloadc1', 'xeenloadc2', 'xeenloadd1', 'xeenloadd2']

# Loading bar frame baked into the 1280x960 images (x0, y0, x1, y1); it only receives the colour grade.
BAR_RECT = (326, 898, 958, 956)
BAR_FEATHER = 6

# The installed variant. Its parameters are recorded below with the others.
CHOSEN_VARIANT = 'combined'

VARIANTS = {
    # Oil/gouache look: strong edge-aware flattening, warm grade, faint canvas weave, no dithering.
    'painted': {
        'paint_radius': 4, 'paint_strength': 0.90, 'paint_sharpness': 8.0,
        'saturation': 0.80, 'sat_rolloff': 0.35, 'warmth': 0.035, 'contrast': 0.14, 'shadow_depth': 0.05,
        'gamma': 1.05,
        'edge_amount': 0.35, 'edge_radius': 1.2,
        'canvas': 0.020, 'grain': 0.010, 'grain_size': 1.0,
        'dither': None, 'chroma': 0.0, 'vignette': 0.20, 'seed': 7,
    },
    # Period display: 16-bit colour (RGB555) with ordered dithering at 640x480, shown 2x, light grade, no painting.
    '16bit': {
        'paint_radius': 0, 'paint_strength': 0.0, 'paint_sharpness': 8.0,
        'saturation': 0.86, 'sat_rolloff': 0.25, 'warmth': 0.025, 'contrast': 0.12, 'shadow_depth': 0.05,
        'gamma': 1.04,
        'edge_amount': 0.0, 'edge_radius': 1.0,
        'canvas': 0.0, 'grain': 0.0, 'grain_size': 1.0,
        'dither': {'bits': 5, 'work_scale': 0.5, 'strength': 1.0, 'upscale': 'nearest'},
        'chroma': 0.0, 'vignette': 0.12, 'seed': 7,
    },
    # Aged print: muted, warmer, softer, paper grain, slight colour fringe and a heavier vignette.
    'aged': {
        'paint_radius': 3, 'paint_strength': 0.50, 'paint_sharpness': 8.0,
        'saturation': 0.68, 'sat_rolloff': 0.30, 'warmth': 0.060, 'contrast': 0.10, 'shadow_depth': 0.03,
        'gamma': 1.02,
        'edge_amount': 0.0, 'edge_radius': 1.0,
        'canvas': 0.040, 'grain': 0.030, 'grain_size': 1.4,
        'dither': None, 'chroma': 1.0, 'vignette': 0.30, 'seed': 7,
    },
    # Painted planes + MM grade + firm outlines + full-size 16-bit ordered dither + faint grain. Installed: the small
    # radius keeps faces and cobbles intact while flattening the plastic micro-detail; stronger canvas read as a grid.
    'combined': {
        'paint_radius': 2, 'paint_strength': 0.80, 'paint_sharpness': 8.0,
        'saturation': 0.82, 'sat_rolloff': 0.30, 'warmth': 0.030, 'contrast': 0.14, 'shadow_depth': 0.05,
        'gamma': 1.04,
        'edge_amount': 0.30, 'edge_radius': 1.2,
        'canvas': 0.008, 'grain': 0.014, 'grain_size': 1.0,
        'dither': {'bits': 5, 'work_scale': 1.0, 'strength': 1.0, 'upscale': 'nearest'},
        'chroma': 0.0, 'vignette': 0.18, 'seed': 7,
    },
}


def luminance(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def kuwahara(rgb, radius, sharpness=8.0):
    """Smooth (weighted) Kuwahara filter on float RGB in [0, 1]: four Gaussian-weighted quadrants around each pixel
    are blended by their flatness, so flat planes are averaged while outlines stay where they are. Unlike the classic
    hard pick of the flattest quadrant it leaves no square blocks."""
    sigma = radius / 2.0
    lum = luminance(rgb)
    mean_l = ndimage.gaussian_filter(lum, sigma, mode='reflect')
    var = np.maximum(ndimage.gaussian_filter(lum * lum, sigma, mode='reflect') - mean_l * mean_l, 0.0)
    means = np.stack([ndimage.gaussian_filter(rgb[..., c], sigma, mode='reflect') for c in range(3)], axis=-1)
    off = max(1, int(round(radius / 2.0)))
    eps = (2.0 / 255.0) ** 2
    total = np.zeros(rgb.shape[:2])
    acc = np.zeros_like(rgb)
    for dy, dx in ((-off, -off), (-off, off), (off, -off), (off, off)):
        v = np.roll(var, (dy, dx), axis=(0, 1))
        m = np.roll(means, (dy, dx), axis=(0, 1))
        w = (v + eps) ** (-sharpness / 2.0)
        w /= eps ** (-sharpness / 2.0)  # keep the weights in a sane float range
        total += w
        acc += m * w[..., None]
    return acc / total[..., None]


def grade(rgb, p):
    lum = luminance(rgb)[..., None]
    chroma = rgb - lum
    sat = np.abs(chroma).max(axis=-1, keepdims=True)
    # Loud colours are pulled back more than quiet ones (the AI look is mostly oversaturated glow).
    scale = p['saturation'] * (1.0 - p['sat_rolloff'] * np.clip(sat * 2.0 - 0.3, 0.0, 1.0))
    out = lum + chroma * scale
    # Warmth: a little more red, a little less blue, weighted toward the highlights.
    w = p['warmth'] * (0.4 + 0.6 * lum)
    out[..., 0] += w[..., 0]
    out[..., 2] -= w[..., 0] * 1.2
    out = np.clip(out, 0.0, 1.0)
    # S-curve contrast around the middle, then deeper shadows, then gamma.
    c = p['contrast']
    out = out + c * (out - 0.5) * (1.0 - np.abs(out - 0.5) * 2.0) * 2.0
    out = np.clip(out, 0.0, 1.0)
    d = p['shadow_depth']
    out = out - d * (1.0 - out) ** 3
    out = np.clip(out, 0.0, 1.0) ** p['gamma']
    return out


def unsharp(rgb, amount, radius):
    if amount <= 0.0:
        return rgb
    blur = np.stack([ndimage.gaussian_filter(rgb[..., c], radius) for c in range(3)], axis=-1)
    return np.clip(rgb + amount * (rgb - blur), 0.0, 1.0)


def canvas_texture(h, w, rng):
    """Faint woven texture: horizontal and vertical streaks of filtered noise."""
    n1 = ndimage.gaussian_filter(rng.standard_normal((h, w)), (0.6, 3.0))
    n2 = ndimage.gaussian_filter(rng.standard_normal((h, w)), (3.0, 0.6))
    n3 = ndimage.gaussian_filter(rng.standard_normal((h, w)), 6.0)
    t = n1 / n1.std() + n2 / n2.std() + 0.6 * n3 / n3.std()
    return t / t.std()


def add_texture(rgb, p, rng):
    h, w = rgb.shape[:2]
    lum = luminance(rgb)
    mid = 4.0 * lum * (1.0 - lum)  # strongest in the midtones, fades in black and white
    if p['canvas'] > 0.0:
        rgb = rgb + (p['canvas'] * canvas_texture(h, w, rng) * (0.35 + 0.65 * mid))[..., None]
    if p['grain'] > 0.0:
        g = rng.standard_normal((h, w))
        if p['grain_size'] > 1.0:
            g = ndimage.gaussian_filter(g, p['grain_size'] - 0.5)
            g /= g.std()
        rgb = rgb + (p['grain'] * g * (0.3 + 0.7 * mid))[..., None]
    return np.clip(rgb, 0.0, 1.0)


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float64)


def dither16(rgb, d):
    """Quantise to `bits` per channel with an ordered Bayer dither at a reduced working size, then scale back."""
    h, w = rgb.shape[:2]
    scale = d['work_scale']
    wh, ww = int(round(h * scale)), int(round(w * scale))
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255.0 + 0.5).astype(np.uint8))
    small = np.asarray(img.resize((ww, wh), Image.LANCZOS)).astype(np.float64) / 255.0
    levels = (1 << d['bits']) - 1
    threshold = (BAYER4 + 0.5) / 16.0 - 0.5
    tiled = np.tile(threshold, (wh // 4 + 1, ww // 4 + 1))[:wh, :ww][..., None]
    q = np.floor(small * levels + 0.5 + tiled * d['strength'])
    q = np.clip(q, 0, levels) / levels
    resample = Image.NEAREST if d.get('upscale', 'nearest') == 'nearest' else Image.BICUBIC
    out = Image.fromarray((q * 255.0 + 0.5).astype(np.uint8)).resize((w, h), resample)
    return np.asarray(out).astype(np.float64) / 255.0


def chromatic(rgb, amount):
    if amount <= 0.0:
        return rgb
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    ry, rx = (yy - cy) / cy, (xx - cx) / cx
    out = rgb.copy()
    for c, sign in ((0, 1.0), (2, -1.0)):
        coords = [yy + sign * amount * ry, xx + sign * amount * rx]
        out[..., c] = ndimage.map_coordinates(rgb[..., c], coords, order=1, mode='reflect')
    return out


def vignette(rgb, amount):
    if amount <= 0.0:
        return rgb
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ry = (yy - (h - 1) / 2.0) / (h / 2.0)
    rx = (xx - (w - 1) / 2.0) / (w / 2.0)
    r2 = (rx * rx + ry * ry) / 2.0
    v = 1.0 - amount * np.clip(r2, 0.0, 1.0) ** 1.5
    return rgb * v[..., None]


def bar_mask(h, w):
    x0, y0, x1, y1 = BAR_RECT
    m = np.zeros((h, w))
    m[y0:y1, x0:x1] = 1.0
    return ndimage.gaussian_filter(m, BAR_FEATHER / 2.0)


def apply(rgb8, p):
    rgb = rgb8.astype(np.float64) / 255.0
    rng = np.random.default_rng(p['seed'])
    graded_only = grade(rgb, p)

    out = rgb
    if p['paint_radius'] > 0 and p['paint_strength'] > 0.0:
        painted = kuwahara(out, p['paint_radius'], p.get('paint_sharpness', 8.0))
        out = out + p['paint_strength'] * (painted - out)
    out = grade(out, p)
    out = unsharp(out, p['edge_amount'], p['edge_radius'])
    out = add_texture(out, p, rng)
    out = chromatic(out, p['chroma'])
    out = vignette(out, p['vignette'])
    if p['dither'] is not None:
        out = dither16(out, p['dither'])

    m = bar_mask(*out.shape[:2])[..., None]
    out = out * (1.0 - m) + vignette(graded_only, p['vignette']) * m
    return (np.clip(out, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def process(src_dir, name, variant):
    path = os.path.join(src_dir, name + '.png')
    im = Image.open(path)
    rgba = np.asarray(im.convert('RGBA'))
    rgb = apply(rgba[..., :3], VARIANTS[variant])
    if im.mode == 'RGBA':
        return Image.fromarray(np.dstack([rgb, rgba[..., 3]]), 'RGBA')
    return Image.fromarray(rgb, 'RGB')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', required=True, help='folder with the untouched original PNGs')
    ap.add_argument('--out', help='write every variant (or --variant) to <out>/<variant>/<name>.png')
    ap.add_argument('--variant', choices=sorted(VARIANTS), help='only this variant')
    ap.add_argument('--install', help='write the chosen variant (default CHOSEN_VARIANT) over <install>/<name>.png')
    args = ap.parse_args()

    if args.install:
        if os.path.realpath(args.install) == os.path.realpath(args.src):
            sys.exit('refusing to filter the originals in place: --src must be the untouched backup')
        variant = args.variant or CHOSEN_VARIANT
        for name in IMAGES:
            dst = os.path.join(args.install, name + '.png')
            process(args.src, name, variant).save(dst, optimize=True)
            os.chmod(dst, 0o644)
            print('installed', variant, dst)
        return
    if not args.out:
        sys.exit('give --out or --install')
    variants = [args.variant] if args.variant else list(VARIANTS)
    for variant in variants:
        folder = os.path.join(args.out, variant)
        os.makedirs(folder, exist_ok=True)
        for name in IMAGES:
            dst = os.path.join(folder, name + '.png')
            process(args.src, name, variant).save(dst)
            print('wrote', dst)


if __name__ == '__main__':
    main()
