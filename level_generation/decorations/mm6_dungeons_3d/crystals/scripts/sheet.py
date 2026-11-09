#!/usr/bin/env python3
"""Review sheet of one prop: native sprite (first frame, x2) | LOD0 front | three-quarter | side, then a row of all
LODs with their triangle counts, in review/<prop>/sheet.png. Usage: sheet.py <prop> <native x2 file>"""
import glob
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
X2 = HERE.parents[3] / 'assets_dev/engine/decorations_x2'
TILE = 320


def tile(path, background=(52, 50, 56)):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = TILE * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (TILE, TILE), background + (255,))
    canvas.alpha_composite(image, ((TILE - image.width) // 2, TILE - image.height - 6))
    return canvas.convert('RGB')


def distribution(path):
    """Luminance 10/50/90th percentiles and mean saturation (HSV) of a sprite's or render's opaque pixels."""
    import numpy as np
    a = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    p = a[..., :3][a[..., 3] > 200]
    lum = p @ np.array([0.2126, 0.7152, 0.0722])
    sat = (p.max(1) - p.min(1)) / np.maximum(p.max(1), 1)
    return 'lum p10/p50/p90 %s sat %.2f' % (np.percentile(lum, [10, 50, 90]).round().astype(int).tolist(), sat.mean())


def main():
    prop, native = sys.argv[1:3]
    triangles = sys.argv[3:]
    out = HERE / 'review' / prop
    views = sorted(glob.glob(str(out / 'lod0_y*.png')), key=lambda p: int(Path(p).stem.split('_y')[1]))
    levels = sorted(glob.glob(str(out / 'level*_y*.png')))
    dim = sorted(glob.glob(str(out / 'dim_y*.png')))
    top = [tile(X2 / native)] + [tile(p) for p in views] + [tile(p) for p in dim]
    labels = [f'native {native}', 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side'] + ['LOD0 dim dungeon light'] * len(dim)
    for label, path in (('native', X2 / native), ('LOD0 front', views[0])):
        print('DISTRIBUTION', prop, label, distribution(path))
    bottom = [tile(p) for p in levels]
    lod_labels = [f'LOD{i}' + (f' {triangles[i]} tris' if i < len(triangles) else '') for i in range(len(levels))]
    columns = max(len(top), len(bottom))
    sheet = Image.new('RGB', (TILE * columns, 2 * (TILE + 20)), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for row, (tiles, names) in enumerate(((top, labels), (bottom, lod_labels))):
        for i, (t, label) in enumerate(zip(tiles, names)):
            sheet.paste(t, (i * TILE, row * (TILE + 20) + 20))
            draw.text((i * TILE + 6, row * (TILE + 20) + 4), label, fill=(0, 0, 0))
    sheet.save(out / 'sheet.png')
    print('SHEET', out / 'sheet.png')


if __name__ == '__main__':
    main()
