#!/usr/bin/env python3
"""Swatch sheet of the dedicated furniture / machine / mechanism textures named in README.md (original bitmaps)."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
GROUPS = {
    'mechanisms': ['bemh16a', 'trim4_16a', 'gn_mtl03', 't1butts', 'tws1f', 'twb1a', 't1swdu', 't1swdd', 'd8s2on',
                   't65b11b', 't65b11c', 'sfpnlon', 'sfpnloff', 'trekscrn', 'trekscon'],
    'furniture': ['7t1cabs', 't1cabs', '7winerack', '7t1books1', 'bookcas1', '7t1beds', '7t1beds2', 't1beds2',
                  'cbedsqr', 'qtextle1', 'bd1rail', 'cb5side', 'cr_w256b', 'crate_w64', 'ch5side', '7t1butts'],
    'sci-fi': ['a1b', 'a2j', 'a3b', 'sfw7a', 'sfw1b', 'hive1', 'hive19', 'swpipes', 'swgirder', 'swtrpnl',
               'swankdk', 'swll4dk', '7gt002b', 't31a01'],
}
SIZE, COLS = 128, 8


def find(name):
    for base in [ROOT / 'reference/mmerge_data_forus/Data/mm6.bitmaps.lod',
                 ROOT / 'reference/mmerge_data_forus/Data/mm7.bitmaps.lod',
                 ROOT / 'assets_source/worlds/mm8/textures_x2']:
        for ext in ('.bmp', '.png'):
            if (base / (name + ext)).exists():
                return base / (name + ext)
    return None


rows = sum((len(v) + COLS - 1) // COLS for v in GROUPS.values())
out = Image.new('RGB', (COLS * SIZE, rows * (SIZE + 14) + 18 * len(GROUPS)), (24, 24, 24))
draw = ImageDraw.Draw(out)
y = 0
for group, names in GROUPS.items():
    draw.text((4, y + 3), group, fill=(255, 255, 0))
    y += 18
    for i, name in enumerate(names):
        x, yy = (i % COLS) * SIZE, y + (i // COLS) * (SIZE + 14)
        path = find(name)
        if path:
            im = Image.open(path).convert('RGB')
            im.thumbnail((SIZE - 4, SIZE - 4))
            out.paste(im, (x + 2, yy + 2))
        draw.text((x + 2, yy + SIZE), name, fill=(230, 230, 230))
    y += ((len(names) + COLS - 1) // COLS) * (SIZE + 14)
out.save(STUDY / 'sheets' / 'textures.png')
print(STUDY / 'sheets' / 'textures.png')
