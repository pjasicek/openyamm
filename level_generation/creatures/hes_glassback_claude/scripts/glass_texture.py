#!/usr/bin/env python3
"""Procedural black volcanic glass for the crest spines (our own art, no inputs).

1024x1024 atlas of 2x2 tiles (512 each). Every crystal facet maps onto one whole tile: u across the facet (0 and 1 are
its edges), v from the root (0, image bottom) to the tip (1, image top). A tile holds very dark glossy glass with
faint lighter streaks along the facet, brighter worn facet edges, a cloudy dark-teal depth near the root and branching
crack lines that glow toward the root and fade by about 60 % of the height.

Writes textures/hgb_glass_basecolor.png (sRGB), hgb_glass_cracks.png (crack weight, the glow region of the mask) and
hgb_glass_metal_rough.png (R specular mask 1, G roughness, B metallic 0)."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
TILE = 512
rng = np.random.default_rng(20261022)


def noise(shape, sigma, rng):
    n = ndimage.gaussian_filter(rng.standard_normal(shape), sigma, mode='wrap')
    return (n - n.mean()) / (n.std() + 1e-9)


def crack_paths(rng, count):
    """Branching polylines starting near the root, climbing with random lateral drift."""
    paths = []
    for _ in range(count):
        x = rng.uniform(0.12, 0.88)
        y = rng.uniform(0.0, 0.08)
        pts = [(x, y)]
        length = rng.uniform(0.35, 0.75)
        heading = rng.uniform(-0.5, 0.5)
        while y < length:
            heading = np.clip(heading + rng.normal(0, 0.45), -1.1, 1.1)
            step = rng.uniform(0.025, 0.05)
            x = np.clip(x + np.sin(heading) * step, 0.04, 0.96)
            y = y + np.cos(heading) * step
            pts.append((x, y))
            if rng.random() < 0.12 and len(paths) < count * 3:
                paths.append(branch(rng, x, y, length))
        paths.append(pts)
    return paths


def branch(rng, x, y, top):
    pts = [(x, y)]
    heading = rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
    for _ in range(rng.integers(2, 6)):
        heading += rng.normal(0, 0.3)
        x = np.clip(x + np.sin(heading) * 0.03, 0.03, 0.97)
        y = min(y + abs(np.cos(heading)) * 0.03, top)
        pts.append((x, y))
    return pts


def draw(paths, size, width):
    img = Image.new('L', (size, size), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for pts in paths:
        px = [(p[0] * size, (1 - p[1]) * size) for p in pts]
        d.line(px, fill=255, width=width, joint='curve')
    return np.asarray(img, np.float32) / 255


def tile(rng):
    s = TILE
    v = np.linspace(1, 0, s)[:, None] * np.ones((1, s))           # 0 root (bottom) .. 1 tip (top)
    u = np.ones((s, 1)) * np.linspace(0, 1, s)[None, :]
    streak = ndimage.gaussian_filter(rng.standard_normal((s, s)), (40, 2.5), mode='wrap')
    streak = (streak - streak.mean()) / streak.std()
    cloud = noise((s, s), 24, rng)
    base = 0.021 + 0.004 * streak + 0.003 * cloud + 0.006 * v      # linear-ish value, very dark
    edge = np.exp(-np.minimum(u, 1 - u) / 0.035)                   # worn bright facet edges
    base += 0.035 * edge * (0.6 + 0.4 * v)
    rgb = np.stack([base * 0.92, base * 1.0, base * 1.12], -1)     # cold blue-black
    depth = np.clip(1.0 - v / 0.55, 0, 1) ** 1.5 * np.clip(0.55 + 0.25 * cloud, 0, 1)
    rgb += depth[..., None] * np.array([0.0, 0.034, 0.028])         # dark teal light deep inside near the root
    paths = crack_paths(rng, int(rng.integers(3, 6)))
    core = draw(paths, s, 6)
    halo = ndimage.gaussian_filter(draw(paths, s, 14), 6)
    fade = np.clip(1.15 - v / 0.62, 0, 1)
    crack = np.clip(core * 1.0 + halo * 0.55, 0, 1) * fade
    return rgb, crack


def main():
    OUT.mkdir(exist_ok=True)
    rgb = np.zeros((2 * TILE, 2 * TILE, 3))
    cracks = np.zeros((2 * TILE, 2 * TILE))
    for ty in range(2):
        for tx in range(2):
            t_rgb, t_crack = tile(rng)
            rgb[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE] = t_rgb
            cracks[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE] = t_crack
    # cracks painted teal in the shared base (the region ramp recolours them per tier)
    teal = np.array([0.30, 0.95, 0.80])
    col = rgb * (1 - cracks[..., None]) + teal * (0.25 + 0.75 * cracks[..., None]) * cracks[..., None]
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.clip(col, 0, None) ** (1 / 2.4) - 0.055)
    srgb = np.clip(srgb, 30 / 255, 1)                              # Khronos floor (charcoal 30)
    Image.fromarray((srgb * 255 + 0.5).astype(np.uint8)).save(OUT / 'hgb_glass_basecolor.png', optimize=True)
    Image.fromarray((np.clip(cracks, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(OUT / 'hgb_glass_cracks.png')
    rough = 0.16 + 0.06 * np.clip(noise((2 * TILE, 2 * TILE), 30, rng) * 0.5 + 0.5, 0, 1) + 0.25 * cracks
    mr = np.stack([np.ones_like(rough), rough, np.zeros_like(rough)], -1)
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'hgb_glass_metal_rough.png')
    # runtime sizes: every crest attachment GLB carries its own copy (one GLB per bone), so keep them small
    Image.open(OUT / 'hgb_glass_basecolor.png').resize((512, 512), Image.LANCZOS).save(OUT / 'hgb_glass_basecolor_512.png')
    Image.open(OUT / 'hgb_glass_metal_rough.png').resize((256, 256), Image.LANCZOS).save(OUT / 'hgb_glass_metal_rough_256.png')
    Image.open(OUT / 'hgb_glass_cracks.png').resize((256, 256), Image.LANCZOS).save(OUT / 'hgb_glass_cracks_256.png')
    print('GLASS', 'crack texels', int((cracks > 0.5).sum()), 'base sRGB median', float(np.median(srgb) * 255))


if __name__ == '__main__':
    main()
