"""review/shots/tiers_vs_native.png: each tier's viewer shot above the MM7 native frame drawn with that tier's palette.

scripts/project.json "sheet": {"frame": <native bitmap>, "tiers": [[<shot name>, <palette id>], ...]}.
"""
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
SPRITES = [REPO / 'assets_dev/worlds/mm7/sprites', REPO / 'assets_dev/engine/sprites',
           REPO / 'reference/mmerge_data_forus/Data/mm7.sprites.lod']
PALETTES = [REPO / 'assets_dev/worlds/mm7/textures', REPO / 'assets_dev/worlds/mm8/textures']
SIZE = 320


def find(directories, name):
    for directory in directories:
        for entry in os.listdir(directory):
            if entry.lower() == name.lower():
                return directory / entry
    raise FileNotFoundError(name)


def native(frame, pid):
    ids = np.asarray(Image.open(find(SPRITES, frame + '.bmp')))
    palette = np.frombuffer(find(PALETTES, f'pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    rgb = palette[ids].copy()
    rgb[ids == 0] = (85, 88, 91)
    rows, cols = np.nonzero(ids)
    image = Image.fromarray(rgb).crop((max(cols.min() - 8, 0), max(rows.min() - 8, 0), cols.max() + 8, rows.max() + 8))
    factor = SIZE / max(image.size)
    return image.resize((int(image.width * factor), int(image.height * factor)), Image.NEAREST)


def shot(name):
    image = Image.open(P / f'review/shots/{name}.png').convert('RGB')
    w, h = image.size
    image = image.crop((int(w * .15), 0, int(w * .85), int(h * .93)))
    factor = SIZE / max(image.size)
    return image.resize((int(image.width * factor), int(image.height * factor)), Image.LANCZOS)


config = json.loads((P / 'scripts/project.json').read_text())['sheet']
columns = [(shot(name), native(config['frame'], pid)) for name, pid in config['tiers']]
top = max(a.height for a, _ in columns)
sheet = Image.new('RGB', (sum(max(a.width, b.width) + 10 for a, b in columns),
                          top + max(b.height for _, b in columns) + 10), (40, 40, 40))
x = 0
for a, b in columns:
    sheet.paste(a, (x, 0))
    sheet.paste(b, (x, top + 10))
    x += max(a.width, b.width) + 10
sheet.save(P / 'review/shots/tiers_vs_native.png')
print(P / 'review/shots/tiers_vs_native.png')
