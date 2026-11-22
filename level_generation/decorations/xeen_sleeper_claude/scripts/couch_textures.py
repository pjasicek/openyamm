#!/usr/bin/env python3
"""Stage 2b: the couch's textures (one set per element). Hull: the Ancient kit's hull steel `xahull` (D-49) with a
normal map from its luminance (panel seams and rivets). Trim: the element's metal (sleeper.json elements: fire warm
bronze, air silver, earth dark bronze, water verdigris), brushed, worn by `xahullbn`'s broad tone. Glow: the element's
XD-19 core (`xcore<element>`): the core window cropped, laid on its side and mirror-tiled into a seamless strip;
air's violet and earth's green are turned to the brief's pale white-blue and amber (only those hues move; the rock
and frame keep theirs). Writes work/tex/hull_*.png, trim_<element>_*.png, glow_<element>.png.
Usage: couch_textures.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = HERE.parents[3]
TEX = REPO / 'assets_dev' / 'worlds' / 'xeen' / 'textures_x2'
out = PROJECT / 'work' / 'tex'
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / 'sleeper.json').read_text())


def load(name):
    return np.asarray(Image.open(TEX / f'{name}.png').convert('RGB')).astype(np.float64) / 255


def normal_from_height(h, strength):
    """Tangent-space normal (glTF, +y up = v up) from a wrapping height map in 0..1."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(h)], -1)   # image rows run down, so +y (up) is -row
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5) * 255


def save(a, name):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB').save(out / name, optimize=True)


hull = load('xahull')
lum = hull @ [0.2126, 0.7152, 0.0722]
height = ndimage.gaussian_filter(lum, 1.0, mode='wrap')
save(hull * 255, 'hull_basecolor.png')
save(normal_from_height(height, 6.0), 'hull_normal.png')
mr = np.zeros_like(hull)
mr[..., 1] = np.clip(0.50 + (0.5 - lum) * 0.3, 0.35, 0.7) * 255   # painted steel; darker grime rougher
mr[..., 2] = 0.30 * 255
save(mr, 'hull_mr.png')
print('HULL luminance p1/p50/p99', np.percentile(lum * 255, [1, 50, 99]).round())

bn = load('xahullbn')
# machined trim: a brushed grain (noise drawn out along u), plus xahullbn's broad tone at low contrast for wear
rng = np.random.default_rng(58)
brushed = ndimage.gaussian_filter(rng.standard_normal((256, 256)), (0.6, 14), mode='wrap')
wear = ndimage.gaussian_filter(np.asarray(Image.fromarray((bn * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS))
                               .astype(np.float64) @ [0.2126, 0.7152, 0.0722] / 255, 3, mode='wrap')
grain = brushed / brushed.std() * 0.6 + (wear - wear.mean()) / wear.std() * 0.4
gh = ndimage.gaussian_filter(brushed, (0.5, 2), mode='wrap') * 0.02 + 0.5
bn = np.asarray(Image.fromarray((bn * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS)).astype(np.float64) / 255
for el, e in cfg['elements'].items():
    tint = np.array(e['trim'], np.float64)
    base = tint[None, None] * np.clip(1.0 + 0.07 * grain, 0.8, 1.15)[..., None]
    if el == 'water':
        # verdigris over bronze: bronze shows where xahullbn is warm and bright (worn edges)
        warm = np.clip((bn[..., 0] - bn[..., 2] - 0.12) * 4, 0, 1)
        warm = ndimage.gaussian_filter(warm, 1.5, mode='wrap')
        bronze = np.array([168, 116, 66], np.float64)[None, None] * np.clip(1.0 + 0.1 * grain, 0.75, 1.2)[..., None]
        base = base * (1 - warm[..., None] * 0.6) + bronze * (warm[..., None] * 0.6)
        metal = e['trim_metal'] + warm * 0.5
    else:
        metal = np.full(grain.shape, e['trim_metal'])
    save(base, f'trim_{el}_basecolor.png')
    save(normal_from_height(gh, 2.0), f'trim_{el}_normal.png')
    mr = np.zeros(bn.shape)
    mr[..., 1] = np.clip(e['trim_rough'] + 0.06 * grain, 0.2, 0.9) * 255
    mr[..., 2] = np.clip(metal, 0, 1) * 255
    save(mr, f'trim_{el}_mr.png')
    lum_t = base @ [0.2126, 0.7152, 0.0722]
    print(f'TRIM {el} luminance p1/p50/p99', np.percentile(lum_t, [1, 50, 99]).round())

    core = Image.open(TEX / f"{e['core']}.png").convert('RGB')
    w, h = core.size
    win = np.asarray(core.crop((int(w * 0.22), int(h * 0.13), int(w * 0.78), int(h * 0.87)))).astype(np.float64) / 255
    hm = e.get('hue_map')
    if hm:
        hsv = np.asarray(Image.fromarray((win * 255).astype(np.uint8)).convert('HSV')).astype(np.float64)
        hue = hsv[..., 0] * 360 / 255
        lo, hi = hm['from']
        sel = ((hue >= lo) & (hue <= hi)).astype(np.float64)
        sel = ndimage.gaussian_filter(sel, 1.0) * np.clip(hsv[..., 1] / 60, 0, 1)
        hsv2 = hsv.copy()
        hsv2[..., 0] = hm['to'] * 255 / 360
        hsv2[..., 1] = hsv[..., 1] * hm['sat']
        hsv2[..., 2] = np.clip(hsv[..., 2] * hm['val'], 0, 255)
        moved = np.asarray(Image.fromarray(hsv2.astype(np.uint8), 'HSV').convert('RGB')).astype(np.float64) / 255
        win = win * (1 - sel[..., None]) + moved * sel[..., None]
    # on its side (long axis horizontal), then mirror-tiled 4x into a seamless strip
    side = np.rot90(win)
    tiles = [side if k % 2 == 0 else side[:, ::-1] for k in range(4)]
    strip = np.concatenate(tiles, 1)
    img = Image.fromarray((strip * 255).astype(np.uint8)).resize((1024, 128), Image.LANCZOS)
    img.save(out / f'glow_{el}.png', optimize=True)
    a = np.asarray(img).astype(np.float64)
    print(f'GLOW {el} mean RGB', a.reshape(-1, 3).mean(0).round(), 'strip', img.size)
