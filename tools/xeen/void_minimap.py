#!/usr/bin/env python3
"""Paint the void under the world rim on a Xeen outdoor map's minimap (U-12, rim agent 2026-11-23).

The minimap and the journal map read the prebuilt `assets_dev/worlds/xeen/icons_x2/xeen_<key>.png` (1,024 square, 8
pixels a cell, north up). Its rim band was rendered as blue sea. This paints every pixel whose centre lies in the
map's void (the L4 sketch's `void` polygons, or its rim sea until the void is built: common/rim.py) near-black with a
sparse fixed star speckle (seeded by the map, so a rerun paints the same picture), and draws the hull's edge, a thin
pale teal line, along the land's side of the void. Run it after every minimap render of a rim map.

    python3 tools/xeen/void_minimap.py <key> [--out <png>]     # default: output/xeen_rim/minimap/xeen_<key>.png
    python3 tools/xeen/void_minimap.py <key> --install         # rewrites the installed minimap in place
"""
import argparse
import os
import sys

import numpy as np
import yaml
from PIL import Image, ImageDraw

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'projects', 'xeen', 'common'))
import rim  # noqa: E402

VOID = np.array([7, 9, 18], np.float32)
EDGE = np.array([120, 170, 168], np.float32)


def void_mask(polygons, size):
    """Pixels whose area lies in a polygon (cells scaled to pixels; PIL fills the polygon's pixels)."""
    scale = size / 128.0
    canvas = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(canvas)
    for polygon in polygons:
        draw.polygon([(x * scale, y * scale) for x, y in polygon], fill=255)
    return np.asarray(canvas) > 127


def paint(image, polygons, seed):
    pixels = np.asarray(image.convert('RGB'), np.float32).copy()
    size = pixels.shape[0]
    mask = void_mask(polygons, size)
    rng = np.random.default_rng(seed)
    out = pixels.copy()
    out[mask] = VOID + rng.normal(0, 1.5, (int(mask.sum()), 3))
    stars = mask & (rng.random(mask.shape) < 0.004)
    brightness = rng.uniform(90, 235, mask.shape)
    tint = rng.uniform(0.85, 1.0, mask.shape + (3,))
    out[stars] = (brightness[..., None] * tint)[stars]
    bright = stars & (rng.random(mask.shape) < 0.15)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        halo = np.roll(np.roll(bright, dy, 0), dx, 1) & mask & ~stars
        out[halo] = np.maximum(out[halo], 70.0)
    # the hull's edge: void pixels next to land, two pixels deep
    land = ~mask
    edge = np.zeros_like(mask)
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            edge |= np.roll(np.roll(land, dy, 0), dx, 1)
    edge &= mask
    # not along the map's own border (np.roll wraps round)
    edge[:2, :] = edge[-2:, :] = False
    edge[:, :2] = edge[:, -2:] = False
    out[edge] = EDGE
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB'), int(mask.sum())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('key')
    parser.add_argument('--out')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    sketch = yaml.safe_load(open(os.path.join(REPO, 'devdocs/xeen/briefs', args.key, 'L4/sketch.yml')))
    polygons = rim.void_polygons(sketch)
    if not polygons:
        print('%s: no void' % args.key)
        return 0
    source = os.path.join(REPO, 'assets_dev/worlds/xeen/icons_x2', 'xeen_%s.png' % args.key)
    image, count = paint(Image.open(source), polygons, sum(map(ord, args.key)))
    if args.install:
        target = source
    else:
        target = args.out or os.path.join(REPO, 'output/xeen_rim/minimap', 'xeen_%s.png' % args.key)
        os.makedirs(os.path.dirname(target), exist_ok=True)
    temporary = target + '.new'
    image.save(temporary, 'PNG')
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)
    print('%s: %d void pixels painted -> %s' % (args.key, count, target))
    return 0


if __name__ == '__main__':
    sys.exit(main())
