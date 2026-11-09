#!/usr/bin/env python3
"""Recoloured texture sets of the MM6 bones batch's Meshy skeleton and skull (read only:
../../../mm6_dungeons_3d/bones/textures/{skeleton,skull}_{basecolor,normal,mr}.png) for the MM7 bone decorations.

For each set: the Meshy base colour's luminance keeps its detail (pores, sutures, cavities) and is rank-matched to
the native sprite's bone pixels (low saturation), coloured by their luminance-to-colour ramp. Stains (the sprite's
saturated pixels: dried flesh and rust on dec19, grime and brown spots on 7dec18/7dec20) are small, soft spots of
fine value noise, gathered where bake_weights.py's weight is high (cavities, and the crown of the skulls), on
`coverage` of the texels at most STAIN_ALPHA strength. The result is scaled so its mean is the
sprite's mean / `occlusion` (COLOR_0 carries the vertex occlusion). Normal maps are copied; roughness is raised.
Writes textures/<name>_{basecolor,normal,mr}.png. Usage: bones_textures.py [name ...]"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_dungeons_3d', 'bones', 'textures')
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
OUT = os.path.join(HERE, 'textures')

# name: source set, sprite, blotch coverage, blotch scale (noise cells across the texture), stain saturation split,
# expected mean occlusion, size, optional sprite region (rows, columns: fractions), optional warm (a linear
# multiplier against the review sky's blue for the outdoor dec19)
SETS = {
    'dec19_bone': {'source': 'skeleton', 'sprite': 'dec19_p2.png', 'coverage': 0.3, 'cells': 40, 'split': 0.4,
                   'occlusion': 0.8, 'size': 1024, 'warm': (1.0, 0.93, 0.8), 'contrast': 0.6, 'cavity': 1.0},
    'dec19_skull': {'source': 'skull', 'sprite': 'dec19_p2.png', 'coverage': 0.3, 'cells': 60, 'split': 0.4,
                    'occlusion': 0.8, 'size': 512, 'columns': (0.8, 1.0), 'warm': (1.0, 0.93, 0.8),
                    'contrast': 0.7, 'crown': 0.6, 'cavity': 1.0},
    'pile_bone': {'source': 'skeleton', 'sprite': '7dec18_p2.png', 'coverage': 0.12, 'cells': 70, 'split': 0.38,
                  'occlusion': 0.7, 'size': 1024, 'contrast': 0.55, 'cavity': 1.2},
    'pile_skull': {'source': 'skull', 'sprite': '7dec18_p2.png', 'coverage': 0.15, 'cells': 80, 'split': 0.38,
                   'occlusion': 0.7, 'size': 1024, 'rows': (0.0, 0.7), 'columns': (0.3, 0.7),
                   'contrast': 0.6, 'crown': 0.8, 'cavity': 1.0},
    'big_skull': {'source': 'skull', 'sprite': '7dec20_p2.png', 'coverage': 0.16, 'cells': 110, 'split': 0.4,
                  'occlusion': 0.8, 'size': 2048, 'contrast': 0.7, 'crown': 1.0, 'cavity': 0.8},
}
WEIGHTS = os.path.join(HERE, 'work', 'weight_{}.npy')   # bake_weights.py: cavity and crown in texture space
STAIN_ALPHA = 0.7                                        # stains never fully cover the bone
STAIN_SOFTNESS = 0.06                                    # drive range over which a stain fades in
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def sprite(spec):
    im = Image.open(os.path.join(X2, spec['sprite'])).convert('RGBA')
    im = im.crop(im.split()[-1].getbbox())
    a = np.asarray(im).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    mask = a[..., 3] > 0.5
    r0, r1 = spec.get('rows', (0, 1)); c0, c1 = spec.get('columns', (0, 1))
    keep = np.zeros_like(mask); keep[int(r0 * h):int(r1 * h), int(c0 * w):int(c1 * w)] = True
    rgb = a[mask & keep][:, :3]
    sat = (rgb.max(1) - rgb.min(1)) / np.maximum(rgb.max(1), 1e-3)
    return rgb, sat


def ramp_colour(native, lum_target):
    """Colour for each target luminance from the native pixels' luminance-to-colour table."""
    nl = native @ LUMA
    bins = np.linspace(nl.min(), nl.max() + 1e-4, 17)
    idx = np.clip(np.digitize(nl, bins) - 1, 0, 15)
    table = np.array([native[idx == k].mean(0) / max(nl[idx == k].mean(), 1e-3) if (idx == k).sum() > 3
                      else native.mean(0) / max(nl.mean(), 1e-3) for k in range(16)])
    centres = (bins[:-1] + bins[1:]) / 2
    chroma = np.stack([np.interp(np.clip(lum_target, centres[0], centres[-1]), centres, table[:, c])
                       for c in range(3)], 1)
    return np.clip(chroma * lum_target[:, None], 0, 1)


def rank_match(values, native_lum):
    order = np.argsort(np.argsort(values))
    rank = order / max(1, len(values) - 1)
    return np.interp(rank, np.linspace(0, 1, len(native_lum)), np.sort(native_lum))


def value_noise(size, cells, rng):
    total = np.zeros((size, size), np.float32)
    amp = 1.0
    for octave in range(3):
        n = cells * 2 ** octave
        grid = rng.random((n, n)).astype(np.float32)
        total += amp * np.asarray(Image.fromarray(grid).resize((size, size), Image.BICUBIC))
        amp *= 0.5
    return total


def build(name):
    spec = SETS[name]
    size = spec['size']
    src = np.asarray(Image.open(os.path.join(SRC, f"{spec['source']}_basecolor.png")).convert('RGB').resize(
        (size, size), Image.LANCZOS)).astype(np.float32) / 255.0
    rgb, sat = sprite(spec)
    bone, stain = rgb[sat < spec['split']], rgb[sat >= spec['split']]
    lum = (src.reshape(-1, 3) @ LUMA)
    rng = np.random.default_rng(5)
    noise = value_noise(size, spec['cells'], rng).ravel()
    noise = np.argsort(np.argsort(noise)) / (len(noise) - 1)              # ranks, 0..1
    weight = np.zeros_like(noise)
    if os.path.exists(WEIGHTS.format(spec['source'])):
        w = np.load(WEIGHTS.format(spec['source'])).astype(np.float32)
        w = np.stack([np.asarray(Image.fromarray(w[..., c]).resize((size, size), Image.BILINEAR)) for c in (0, 1)],
                     -1).reshape(-1, 2)
        weight = np.clip(w[:, 0] * spec.get('cavity', 0.0) + w[:, 1] * spec.get('crown', 0.0), 0, 1)
    # stains: small soft spots from the noise, gathered where the weight (crevices, crown) is high
    drive = 0.45 * noise + 0.55 * weight
    threshold = np.quantile(drive, 1 - spec['coverage'])
    alpha = np.clip((drive - threshold) / STAIN_SOFTNESS, 0, 1) * STAIN_ALPHA
    detail = lum
    k = spec.get('contrast', 1.0)               # < 1: less of the sprite's painted light in the texture

    def soften(values, native):
        med = float(np.median(native @ LUMA))
        return med + (values - med) * k

    plain = ramp_colour(bone, soften(rank_match(detail, bone @ LUMA), bone))
    dirt = ramp_colour(stain, soften(rank_match(detail, stain @ LUMA), stain))
    out = plain * (1 - alpha[:, None]) + dirt * alpha[:, None]
    lin = srgb_to_linear(out)
    target = srgb_to_linear(rgb.mean(0)) / spec['occlusion'] * np.array(spec.get('warm', (1, 1, 1)))
    lin *= (target / lin.mean(0))[None, :]
    out = linear_to_srgb(lin).reshape(size, size, 3)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(OUT, f'{name}_basecolor.png'))
    normal = Image.open(os.path.join(SRC, f"{spec['source']}_normal.png")).convert('RGB')
    normal.resize((min(size, 1024), min(size, 1024)), Image.LANCZOS).save(os.path.join(OUT, f'{name}_normal.png'))
    mr = np.asarray(Image.open(os.path.join(SRC, f"{spec['source']}_mr.png")).convert('RGB').resize(
        (256, 256), Image.LANCZOS)).astype(np.float32)
    mr[..., 0] = 90                                              # specular mask (unused unless the material asks)
    mr[..., 1] = np.clip(mr[..., 1] * 0.5 + 150, 0, 255)          # rough, dry bone
    mr[..., 2] = 0
    Image.fromarray(mr.astype(np.uint8)).save(os.path.join(OUT, f'{name}_mr.png'))
    print('SET', name, 'mean', (out.reshape(-1, 3).mean(0) * 255).round(), 'sprite', (rgb.mean(0) * 255).round(),
          'bone', (bone.mean(0) * 255).round(), 'stain', (stain.mean(0) * 255).round())


if __name__ == '__main__':
    for name in sys.argv[1:] or SETS:
        build(name)
