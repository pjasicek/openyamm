#!/usr/bin/env python3
"""The water orbs' texture as MM9's animated sprite: Sprites/Water/water123.spr names ten frames (water123_0000-0009,
128 x 128) at 15 frames a second (the .spr header). Each frame is decoded (convert_abc_model.decode_dtx), upscaled with
the isle's textures.upscale (x4, as the frame-0 texture before) and reduced to 256 (the orb is 41 units tall), and the
ten are packed left to right, top to bottom, five by two, into textures/waterorb_basecolor.png. finish.py gives the
material `openyamm_flipbook: [5, 2, 15]`; build_waterorb.py centres the orb's UVs in one frame (MM9's mapping spans
-0.12..0.12 of the texture, across its edge, which would reach the next cell). Usage: waterorb_flipbook.py"""
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image

import props_table

REPO = props_table.REPO
sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from convert_abc_model import decode_dtx  # noqa: E402
import textures as isle_textures  # noqa: E402

SPR = REPO / 'mm9/extracted/SPRITES/SPRITES/WATER/WATER123.spr'
FRAMES = REPO / 'mm9/extracted/SPRITETEXTURES/SPRITETEXTURES/WATER/WATER123'
COLUMNS, ROWS, CELL = 5, 2, 256


def main():
    count, rate = struct.unpack_from('<II', SPR.read_bytes(), 0)
    if (count, rate) != (COLUMNS * ROWS, 15):
        raise SystemExit(f'{SPR.name}: {count} frames at {rate} fps, not the 10 at 15 this atlas is laid out for')
    atlas = Image.new('RGB', (COLUMNS * CELL, ROWS * CELL))
    with tempfile.TemporaryDirectory() as work:
        for k in range(count):
            raw = Path(work) / f'frame{k}.png'
            big = Path(work) / f'frame{k}_x4.png'
            decode_dtx(FRAMES / f'WATER123_{k:04d}.dtx').convert('RGB').save(raw)
            isle_textures.upscale(raw, big)
            cell = Image.open(big).convert('RGB').resize((CELL, CELL), Image.LANCZOS)
            atlas.paste(cell, ((k % COLUMNS) * CELL, (k // COLUMNS) * CELL))
    target = props_table.HERE / 'textures/waterorb_basecolor.png'
    atlas.save(target)
    print('WROTE', target, atlas.size, f'{count} frames at {rate} fps')


if __name__ == '__main__':
    main()
