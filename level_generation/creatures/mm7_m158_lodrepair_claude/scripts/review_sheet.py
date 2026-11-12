#!/usr/bin/env python3
"""Review sheet of repaired models: per model, installed and repaired LOD0-3 (three-quarter view, same camera), then
each far switch as the player sees it: the level before and the new level at the switch size (LOD2 180 px,
LOD3 72 px of the bounds diagonal; LOD3 enlarged 2x with nearest sampling).
Usage: review_sheet.py <out.png> <stem>...   (reads work/<stem>/result.json and its chosen audit)"""
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
WORK = PROJECT / 'work' / os.environ.get('LOD_REPAIR_RUN', '')
CELL = 220
BACKGROUND = (120, 120, 128, 255)
SWITCH = {2: (180, 1), 3: (72, 2)}  # switch size, enlargement


def view(path, size, enlarge=1):
    image = Image.open(path).convert('RGBA').resize((size, size), Image.LANCZOS)
    tile = Image.new('RGBA', (size, size), BACKGROUND)
    tile.alpha_composite(image)
    return tile.resize((size * enlarge, size * enlarge), Image.NEAREST) if enlarge > 1 else tile


def model_rows(stem):
    result = json.loads((WORK / stem / 'result.json').read_text())
    step = result['chosen']
    audit = WORK / stem / f'audit_{step}'
    entry = next(s for s in result['steps'] if s.get('step') == step)
    width = 4 * CELL + 10 + sum(2 * size * enlarge + 24 for size, enlarge in SWITCH.values())
    rows = Image.new('RGBA', (width, CELL * 2 + 40), BACKGROUND)
    draw = ImageDraw.Draw(rows)
    for row, (label, folder) in enumerate((('installed', 'installed'), ('repaired', step))):
        for level in range(4):
            rows.alpha_composite(view(audit / folder / f'lod{level}_q34.png', CELL), (level * CELL, 40 + row * CELL))
            draw.text((level * CELL + 4, 40 + row * CELL + CELL - 14), f'{label} LOD{level}', fill=(255, 230, 120))
    x = 4 * CELL + 10
    for level, (size, enlarge) in SWITCH.items():
        for row, folder in enumerate(('installed', step)):
            before = view(audit / folder / f'lod{level - 1}_q34.png', size, enlarge)
            after = view(audit / folder / f'lod{level}_q34.png', size, enlarge)
            rows.alpha_composite(before, (x, 40 + row * CELL))
            rows.alpha_composite(after, (x + before.width + 4, 40 + row * CELL))
        draw.text((x, 40 + 2 * CELL - 14), f'LOD{level - 1} | LOD{level} at {size} px' +
                  (f', {enlarge}x' if enlarge > 1 else ''), fill=(255, 255, 255))
        x += 2 * size * enlarge + 24
    ratios = entry['ratios']
    status = 'passes gate' if result['passed'] else 'DOES NOT PASS GATE'
    draw.text((4, 4), f'{stem}  ({result["node"]})  LOD2 {ratios[0]:.0%} / LOD3 {ratios[1]:.0%} of LOD0, {status}',
              fill=(255, 255, 255))
    scores = '  '.join(f'LOD{k}: outline {entry["installed"][str(k)][0]:.0f}% -> {entry["repaired"][str(k)][0]:.0f}%, '
                       f'colour {entry["installed"][str(k)][1]:.0f} -> {entry["repaired"][str(k)][1]:.0f}'
                       for k in (2, 3))
    draw.text((4, 20), scores, fill=(220, 220, 220))
    return rows


def main():
    out = Path(sys.argv[1])
    sheets = [model_rows(stem) for stem in sys.argv[2:]]
    sheet = Image.new('RGBA', (max(s.width for s in sheets), sum(s.height + 10 for s in sheets)), (60, 60, 64, 255))
    y = 0
    for part in sheets:
        sheet.alpha_composite(part, (0, y))
        y += part.height + 10
    sheet.convert('RGB').save(out)
    print('SHEET', out)


if __name__ == '__main__':
    main()
