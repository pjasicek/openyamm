#!/usr/bin/env python3
"""Contact sheet: rows of PNG renders on a neutral background with labels.
Usage: sheet.py out.png "label:img1,img2,..." ... [--cell 256]"""
import sys

from PIL import Image, ImageDraw


def main():
    args = sys.argv[1:]
    cell = 256
    if '--cell' in args:
        i = args.index('--cell'); cell = int(args[i + 1]); del args[i:i + 2]
    out, rows = args[0], args[1:]
    parsed = [(r.split(':', 1)[0], r.split(':', 1)[1].split(',')) for r in rows]
    cols = max(len(files) for _, files in parsed)
    label_w = 150
    sheet = Image.new('RGB', (label_w + cols * cell, len(parsed) * cell), (138, 148, 160))
    draw = ImageDraw.Draw(sheet)
    for r, (label, files) in enumerate(parsed):
        draw.text((6, r * cell + 6), label.replace('|', '\n'), fill=(10, 10, 10))
        for c, f in enumerate(files):
            if not f:
                continue
            im = Image.open(f).convert('RGBA'); im.thumbnail((cell, cell))
            bg = Image.new('RGBA', (cell, cell), (138, 148, 160, 255))
            bg.alpha_composite(im, ((cell - im.width) // 2, (cell - im.height) // 2))
            sheet.paste(bg.convert('RGB'), (label_w + c * cell, r * cell))
    sheet.save(out)


if __name__ == '__main__':
    main()
