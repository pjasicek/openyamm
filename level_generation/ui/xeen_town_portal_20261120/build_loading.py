#!/usr/bin/env python3
"""Xeen's loading pages from the Codex paintings (README.md), as level_generation/ui/hesper_loading/build_pages.py:

    python3 build_loading.py xeenloadc1=raw/load_c1_v1.png xeenloadc2=raw/load_c2_v1.png ...

Each painting is cropped to 4:3 (centred) and resized to 1280x960 with Lanczos; the native loading-bar frame
(assets_dev/engine/icons_x2/loading2.png at (322, 896)-(962, 960), outer 8 pixels feathered) is composited over its
bottom, so the engine's loadprog fill (drawn at (346, 918), 598x28) sits in it. Written as RGBA with full alpha, like
7load1.png, to final/<name>.png, with a 50 % progress preview in review/<name>_50.png.
"""
import sys
from pathlib import Path

from PIL import Image

W = Path(__file__).resolve().parent
ICONS = W.parents[2] / 'assets_dev/engine/icons_x2'
SIZE = (1280, 960)
CROP = (322, 896, 962, 960)
FILL = (346, 918)
FEATHER = 8


def main() -> int:
    native = Image.open(ICONS / 'loading2.png').convert('RGB')
    frame = native.crop(CROP)
    mask = Image.new('L', frame.size)
    width, height = frame.size
    mask.putdata([round(255 * min(1, min(x, y, width - 1 - x, height - 1 - y) / FEATHER))
                  for y in range(height) for x in range(width)])
    fill = Image.open(ICONS / 'loadprog.png').convert('RGBA')
    for argument in sys.argv[1:]:
        name, source = argument.split('=')
        painting = Image.open(W / source).convert('RGB')
        target = painting.width / painting.height
        if target > 4 / 3:
            cut = round(painting.height * 4 / 3)
            left = (painting.width - cut) // 2
            painting = painting.crop((left, 0, left + cut, painting.height))
        elif target < 4 / 3:
            cut = round(painting.width * 3 / 4)
            top = (painting.height - cut) // 2
            painting = painting.crop((0, top, painting.width, top + cut))
        page = painting.resize(SIZE, Image.LANCZOS)
        page.paste(frame, CROP[:2], mask)
        page.convert('RGBA').save(W / f'final/{name}.png')
        preview = page.convert('RGBA')
        preview.alpha_composite(fill.crop((0, 0, 299, 28)), FILL)
        preview.convert('RGB').save(W / f'review/{name}_50.png')
        print(name, source, 'ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
