#!/usr/bin/env python3
"""Metal texture sets of the goblet, vase and eagle: textures/misc_<name>_{basecolor,normal,mr}.png from Poly Haven
rusty_metal_02 (CC0, textures/source/): its saturation marks tarnish or rust, its luminance and roughness give the
clean metal's variation. Clean metal: the metal colour, roughness remapped into a narrow glossy range, metallic
`metal`; tarnish or rust: its own colour, rougher, metallic `dirty_metal`. Normal: the scan's, flattened.
`repeat` (u, v) tiles the set: the lathes' u runs once around and v once along the profile, about twice the
circumference, so (2, 4) keeps the texels square.
Usage: small_metal.py [name ...]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / 'textures' / 'source' / 'rusty_metal_02'
OUT = HERE / 'textures'
MEANS = OUT / 'misc_metal_means.json'      # linear effective diffuse means, read by the builders

SPECS = {
    # brass-gold goblet (dungeon): partly metallic, see the README (indoor decorations get no specular lobes)
    'goblet_metal': dict(size=256, repeat=(2, 4), clean=(230, 200, 128), dirty=(140, 106, 62), threshold=0.48,
                         spread=0.12, contrast=0.25, rough=(0.30, 0.42), dirty_rough=0.62, metal=0.65,
                         dirty_metal=0.35, normal=0.25),
    # steel-grey vase with golden-copper tarnish streaks (dungeon), both metal
    'vase_metal': dict(size=256, repeat=(2, 4), clean=(178, 180, 172), dirty=(186, 154, 96), threshold=0.34,
                       spread=0.12, contrast=0.9, rough=(0.30, 0.45), dirty_rough=0.55, metal=0.6,
                       dirty_metal=0.6, normal=0.4),
    # gold eagle (outdoor): fully metallic clean gold, tarnish in the scan's rust spots
    'eagle_metal': dict(size=512, repeat=(1, 1), clean=(255, 206, 118), dirty=(112, 76, 32), threshold=0.5,
                        spread=0.12, contrast=0.3, rough=(0.30, 0.40), dirty_rough=0.6, metal=1.0,
                        dirty_metal=0.5, normal=0.3),
}
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def load(kind, size):
    return Image.open(SRC / f'rusty_metal_02_{kind}_1k.png').convert('RGB').resize((size, size), Image.LANCZOS)


def make(name):
    s = SPECS[name]
    size = s['size']
    rgb = np.asarray(load('diff', size).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255.0
    satur = rgb.max(2) - rgb.min(2)
    mask = np.clip((satur - s['threshold']) / s['spread'], 0, 1)
    mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)))
    mask = mask.astype(np.float32)[..., None] / 255.0
    lum = rgb @ LUMA
    shade = ((lum / lum.mean()) ** s['contrast'])[..., None]
    clean = srgb_to_linear(np.array(s['clean'], np.float32) / 255.0)
    dirty = srgb_to_linear(np.array(s['dirty'], np.float32) / 255.0)
    base = np.clip(shade * ((1 - mask) * clean + mask * dirty), 0, 1)
    rough = np.asarray(load('rough', size).convert('L')).astype(np.float32) / 255.0
    lo, hi = s['rough']
    rough = lo + (hi - lo) * (rough - rough.min()) / max(1e-6, rough.max() - rough.min())
    rough = (1 - mask[..., 0]) * rough + mask[..., 0] * s['dirty_rough']
    metal = (1 - mask[..., 0]) * s['metal'] + mask[..., 0] * s['dirty_metal']
    nor = np.asarray(load('nor_gl', size)).astype(np.float32) / 127.5 - 1.0
    k = s['normal'] * (1 - mask[..., 0]) + 1.0 * mask[..., 0]          # rust keeps its relief
    nor[..., :2] *= k[..., None]
    nor /= np.linalg.norm(nor, axis=2, keepdims=True)
    ru, rv = s['repeat']
    tile = lambda a: np.tile(a, (rv, ru, 1))
    base_img = (linear_to_srgb(base) * 255 + 0.5).clip(0, 255).astype(np.uint8)
    mr = np.stack([np.zeros_like(rough), rough, metal], 2)
    Image.fromarray(tile(base_img)).save(OUT / f'misc_{name}_basecolor.png')
    Image.fromarray(tile(((nor + 1) * 127.5 + 0.5).clip(0, 255).astype(np.uint8))).save(OUT / f'misc_{name}_normal.png')
    Image.fromarray(tile((mr * 255 + 0.5).astype(np.uint8))).save(OUT / f'misc_{name}_mr.png')
    # The display of a dungeon decoration is diffuse only (fs_model.sc: base x (1 - metallic) x light, its key light
    # without lobes, its reflection at 0.1): the mean effective albedo that COLOR_0 is tinted against.
    eff = (base * (1 - metal[..., None])).reshape(-1, 3).mean(0)
    means = json.loads(MEANS.read_text()) if MEANS.exists() else {}
    means[f'misc_{name}'] = [float(v) for v in eff]
    MEANS.write_text(json.dumps(means, indent=1, sort_keys=True) + '\n')
    print('METAL', name, 'base mean', (linear_to_srgb(base.reshape(-1, 3).mean(0)) * 255).round().astype(int).tolist(),
          'effective diffuse mean', (linear_to_srgb(eff) * 255).round().astype(int).tolist(),
          'dirty fraction', round(float(mask.mean()), 3))


if __name__ == '__main__':
    for n in sys.argv[1:] or SPECS:
        make(n)
