#!/usr/bin/env python3
"""Native sprite frames of one action as a strip (attacks stream, MM6-MM8 audit fixes, 2026-11-11).

    native_strip.py <sprite folder, e.g. level_generation/creatures/mm7_m426> <out.png> [--action attack]
                    [--dirs 0,2] [--height 220]

Reads the folder's manifest.json (animations -> directions -> frames) and the restored aligned_2x frames (the
native/ frames when there are none), one row per direction, frames left to right with their duration in ms.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('folder', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('--action', default='attack')
    p.add_argument('--dirs', default='0,2')
    p.add_argument('--height', type=int, default=220)
    args = p.parse_args()
    manifest = json.loads((args.folder / 'manifest.json').read_text())
    animation = manifest['animations'][args.action]
    rows = []
    for direction in args.dirs.split(','):
        cells = []
        views = animation.get('directions') or animation.get('views')    # MM7/MM8 vs MM6 manifests
        for frame in views[direction]:
            path = None
            for sub in ('aligned_2x', 'native'):
                candidate = args.folder / sub / (frame['frame'] + '.png')
                if candidate.exists():
                    path = candidate
                    break
            image = Image.open(path).convert('RGBA')
            box = image.getbbox()
            if box:
                image = image.crop((0, 0, image.width, image.height))
            if frame.get('mirror') or frame.get('mirrored'):
                image = ImageOps.mirror(image)
            scale = args.height / image.height
            image = image.resize((max(1, int(image.width * scale)), args.height), Image.LANCZOS)
            cell = Image.new('RGBA', (image.width, args.height + 16), (40, 40, 48, 255))
            cell.alpha_composite(image, (0, 0))
            ImageDraw.Draw(cell).text((3, args.height + 2), f"{frame['frame']} {frame['duration_ms']:.0f}",
                                      fill=(230, 230, 230, 255))
            cells.append(cell)
        width = sum(c.width for c in cells)
        row = Image.new('RGBA', (width, args.height + 16), (40, 40, 48, 255))
        x = 0
        for c in cells:
            row.alpha_composite(c, (x, 0))
            x += c.width
        rows.append(row)
    sheet = Image.new('RGBA', (max(r.width for r in rows), sum(r.height for r in rows)), (40, 40, 48, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(args.out)
    print(args.out, sheet.size)


if __name__ == '__main__':
    main()
