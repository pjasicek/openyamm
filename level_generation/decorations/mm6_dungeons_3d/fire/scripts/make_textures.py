#!/usr/bin/env python3
"""Textures for the MM6 dungeon fire fixtures (fire/textures/).

Derived from the outdoor props textures (read only, ../../mm6_new_sorpigal_3d/props/textures): fx_iron, fx_gold,
fx_steel and fx_rock copy a props base colour and normal map (fx_iron, fx_gold and fx_rock brightened, so the
fire-lit iron, the bright sconce gold and the pink cauldron stones stay within a COLOR_0 tint of at most one), with a
new metallic-roughness map of low metal: the engine's indoor ambient lights only the (1 - metallic) diffuse part, so
a fully metallic gold or iron would render near black where the native sprite is bright. New procedural, tileable
maps: wax (candle) and brew (the cauldron's churning surface, played with openyamm_uv_scroll). Also writes
textures/means.json: the linear mean base colour of every texture the build scripts tint (COLOR_0 tint =
linear(native sRGB) / linear mean). Usage: make_textures.py"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'textures'
PROPS = HERE.parents[1] / 'mm6_new_sorpigal_3d' / 'props' / 'textures'
rng = np.random.default_rng(9137)

# name: (props source, base colour gain, roughness or None (keep the source's), metal)
DERIVED = {
    'fx_iron': ('iron', 2.0, None, 0.2),
    'fx_gold': ('gold', 1.3, 0.4, 0.25),
    'fx_steel': ('steel', 1.0, None, 0.2),
    'fx_rock': ('stone', 1.6, 0.85, 0.0),
}
MEANS_OF = ['fx_iron', 'fx_gold', 'fx_steel', 'fx_rock', 'wax', 'brew', 'embers', 'logs', 'wood']


def linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def noise(shape, beta=2.0, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1] (white noise filtered by 1 / f^beta; scale stretches each axis)."""
    field = rng.normal(size=shape)
    fy, fx = np.meshgrid(np.fft.fftfreq(shape[0]) * scale[0], np.fft.fftfreq(shape[1]) * scale[1], indexing='ij')
    radius = np.sqrt(fx * fx + fy * fy)
    radius[0, 0] = 1.0
    spectrum = np.fft.fft2(field) / radius ** beta
    spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifft2(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, colour_linear, height, strength, roughness, metal):
    Image.fromarray((srgb(colour_linear) * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_basecolor.png')
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        OUT / f'{name}_normal.png')
    mr = np.dstack([np.zeros(height.shape), np.full(height.shape, roughness), np.full(height.shape, metal)])
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_mr.png')


def derived():
    for name, (source, gain, roughness, metal) in DERIVED.items():
        base = np.asarray(Image.open(PROPS / f'{source}_basecolor.png').convert('RGB')).astype(np.float64)
        if gain != 1.0:
            base = srgb(linear(base) * gain) * 255
        Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(OUT / f'{name}_basecolor.png')
        shutil.copyfile(PROPS / f'{source}_normal.png', OUT / f'{name}_normal.png')
        source_mr = np.asarray(Image.open(PROPS / f'{source}_mr.png').convert('RGB')).astype(np.float64) / 255
        rough = source_mr[..., 1] if roughness is None else np.full(source_mr.shape[:2], roughness)
        mr = np.dstack([np.zeros(rough.shape), rough, np.full(rough.shape, metal)])
        Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_mr.png')


def wax():
    """Off-white candle wax: soft blotches and vertical drip streaks (texture v runs up the candle)."""
    size = 256
    blotch = noise((size, size), 2.2)
    streak = noise((size, size), 2.0, scale=(0.15, 1.0))     # long along v (rows)
    shade = 0.82 + 0.12 * blotch + 0.10 * (streak - 0.5)
    colour = np.dstack([shade * 0.93, shade * 0.87, shade * 0.74])
    save('wax', colour, blotch * 0.6 + streak * 0.4, 3.0, 0.45, 0.0)


def brew():
    """A murky, bubbling brew: a dark churned base with pale bubble rims, periodic so it can scroll."""
    size = 256
    churn = noise((size, size), 1.8)
    y, x = np.mgrid[0:size, 0:size]
    rims = np.zeros((size, size))
    height = churn * 0.4
    for _ in range(70):
        cx, cy = rng.uniform(0, size, 2)
        radius = rng.uniform(4, 15)
        dx = (x - cx + size / 2) % size - size / 2
        dy = (y - cy + size / 2) % size - size / 2
        distance = np.sqrt(dx * dx + dy * dy)
        ring = np.exp(-((distance - radius) / 1.6) ** 2)
        rims = np.maximum(rims, ring)
        height += np.clip(1 - distance / radius, 0, 1) ** 0.5 * 0.6
    shade = 0.10 + 0.22 * churn + 0.45 * rims
    colour = np.dstack([shade * 1.0, shade * 0.92, shade * 0.80])
    save('brew', colour, height, 4.0, 0.25, 0.0)


def means():
    table = {}
    for name in MEANS_OF:
        path = OUT / f'{name}_basecolor.png'
        if not path.exists():
            path = PROPS / f'{name}_basecolor.png'
        rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
        table[name] = [round(float(v), 5) for v in linear(rgb).reshape(-1, 3).mean(0)]
        print('MEAN', name, table[name], 'sRGB', (srgb(np.array(table[name])) * 255).astype(int))
    path = OUT / 'means.json'
    current = json.loads(path.read_text()) if path.exists() else {}
    current.update(table)                     # keeps the PBR sets' means (make_pbr_textures.py)
    path.write_text(json.dumps(current, indent=1) + '\n')


def main():
    OUT.mkdir(exist_ok=True)
    derived()
    wax()
    brew()
    means()


if __name__ == '__main__':
    main()
