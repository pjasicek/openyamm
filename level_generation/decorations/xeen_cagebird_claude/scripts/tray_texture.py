#!/usr/bin/env python3
"""Stage 2: the tray's iron, cut from the cage picture itself (assets_dev/worlds/xeen/textures_x2/xwcage.png, the
panel the tray stands in front of), so the tray reads as part of the cage. One 256 x 256 atlas:

  rows   0-159  eight slats: the picture's four vertical bars (20 px wide, two runs each between the cross bars),
                turned to run along u                         -> the tray floor and the perch beam
  rows 160-207  the riveted middle cross bar (half its length at 2x) -> the rim's faces
  rows 208-255  the riveted top cross bar (half its length at 2x)    -> the rim's top and the posts

Writes work/tex/tray_basecolor.png."""
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
CAGE = REPO / 'assets_dev/worlds/xeen/textures_x2/xwcage.png'
BARS = [22, 86, 150, 214]          # first opaque column of each 20 px bar
RUNS = [(28, 238), (272, 482)]     # rows between the cross bars (0-23, 244-267, 488-511)
CROSS = [(244, 268), (0, 24)]


def main():
    cage = Image.open(CAGE).convert('RGBA')
    rgb = cage.convert('RGB')
    alpha = np.asarray(cage)[..., 3]
    for x in BARS:
        assert alpha[RUNS[0][0]:RUNS[0][1], x:x + 20].min() > 200, x
    atlas = Image.new('RGB', (256, 256))
    row = 0
    for run in RUNS:
        for x in BARS:
            strip = rgb.crop((x, run[0], x + 20, run[1])).rotate(90, expand=True)   # 210 x 20, along u
            atlas.paste(strip.resize((256, 20), Image.LANCZOS), (0, row))
            row += 20
    for top, bottom in CROSS:
        band = rgb.crop((0, top, 128, bottom)).resize((256, 48), Image.LANCZOS)   # half its length at 2x: round rivets
        atlas.paste(band, (0, row))
        row += 48
    assert row == 256
    out = PROJECT / 'work' / 'tex'
    out.mkdir(parents=True, exist_ok=True)
    atlas.save(out / 'tray_basecolor.png', optimize=True)
    print('tray atlas', out / 'tray_basecolor.png')


if __name__ == '__main__':
    main()
