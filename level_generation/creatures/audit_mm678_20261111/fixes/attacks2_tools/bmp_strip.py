#!/usr/bin/env python3
"""Native frames given as files, side by side, one row per direction (attacks-2 stream, 2026-11-11).

    bmp_strip.py <out.png> <frame file for direction 0> [...] [--dirs 0,2] [--scale 1]

For folders with a manifest.json prefer ../attack_tools/native_strip.py. Here the frames are named explicitly (MM8
bitmaps in assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites/); other directions replace the
trailing 0 of the stem (case-insensitive lookup). Palette index 0 shows as light grey; a missing frame is pink.
"""
import argparse
from pathlib import Path

from PIL import Image


def load(path):
    img = Image.open(path)
    if img.mode == 'P':
        idx = img.copy()
        img = img.convert('RGBA')
        alpha = Image.frombytes('L', idx.size, bytes(0 if v == 0 else 255 for v in idx.tobytes()))
        img.putalpha(alpha)
    img = img.convert('RGBA')
    bg = Image.new('RGBA', img.size, (225, 225, 220, 255))
    bg.alpha_composite(img)
    return bg.convert('RGB')


def find(path, d):
    want = (path.stem[:-1] + str(d) + path.suffix).lower()
    for q in path.parent.iterdir():
        if q.name.lower() == want:
            return q
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('out')
    p.add_argument('frames', nargs='+')
    p.add_argument('--dirs', default='0,2')
    p.add_argument('--scale', type=int, default=1)
    a = p.parse_args()
    rows = []
    for d in [int(x) for x in a.dirs.split(',')]:
        rows.append([load(q) if (q := find(Path(f), d)) else Image.new('RGB', (64, 64), (255, 200, 200))
                     for f in a.frames])
    w = max(sum(i.width for i in r) for r in rows)
    h = sum(max(i.height for i in r) for r in rows)
    sheet = Image.new('RGB', (w, h), (255, 255, 255))
    y = 0
    for r in rows:
        x = 0
        for i in r:
            sheet.paste(i, (x, y))
            x += i.width
        y += max(i.height for i in r)
    if a.scale != 1:
        sheet = sheet.resize((w * a.scale, h * a.scale), Image.NEAREST)
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == '__main__':
    main()
