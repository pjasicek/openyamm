#!/usr/bin/env python3
"""Reference pictures of the Vertigo classic pilot (2026-11-24) from the original Clouds of Xeen art.

Writes pics/<name>.png, which specs.yml names as `pic/<name>` (xtex.py `master()`):
- native_wall, native_door, native_torch: the original town wall frames (XEEN.CC ftown1/ftown2, the nearest
  front wall, 168 x 85), enlarged 4x with nearest neighbour: the design as the original shows it.
- native_hut, native_well: the thatched hut (052.obj) and the well with its shingle roof (012.obj), the only roofs
  in the original's town art, enlarged 6x.
- guide_wall, guide_door, guide_window, guide_corner: layout guides at the master size of one bay (512 x 1024, the
  4x of 128 x 256): one bay of the original wall (half post, panel, half post; beam, panel, beam) resampled
  piecewise so the posts and beams keep their thickness and only the plaster panel stretches, smoothed so the model
  takes the layout and colours, not the pixels.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPRITES = ROOT / 'reference/mm4_5_world_of_xeen/unpacked/sprites/xeen'
PICS = HERE / 'pics'
W, H = 512, 1024
# Measured on ftown1 frame 0 (bright plaster columns and rows): posts at 0-10, 54-62, 107-115, 159-167; panels
# between; top beam rows 0-9, bottom beam rows 76-84.
BAY_COLS = (58, 112)          # half of the post at 54-62, the panel 63-106, half of the post at 107-115
PANEL_COLS = (63, 107)
BEAM_TOP, BEAM_BOTTOM = (0, 10), (76, 85)
POST_PX = 46                  # half a post at the master size (a whole post is about 23 texels of 128)
BEAM_PX = 88


def frame(name, index=0):
    return Image.open(SPRITES / name / f'frame_{index:04d}.png').convert('RGBA')


def enlarge(image, scale):
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def piece(image, box, size):
    return image.crop(box).resize(size, Image.LANCZOS)


def bay(image, top_panel=None):
    """One bay of a native wall frame at the master size: half posts at the sides, beams at top and bottom."""
    rgb = image.convert('RGB')
    x0, x1 = BAY_COLS
    p0, p1 = PANEL_COLS
    out = Image.new('RGB', (W, H))
    rows = [(BEAM_TOP, BEAM_PX), ((BEAM_TOP[1], BEAM_BOTTOM[0]), H - 2 * BEAM_PX), (BEAM_BOTTOM, BEAM_PX)]
    cols = [((x0, p0), POST_PX), ((p0, p1), W - 2 * POST_PX), ((p1, x1), POST_PX)]
    y = 0
    for (r0, r1), height in rows:
        x = 0
        for (c0, c1), width in cols:
            out.paste(piece(rgb, (c0, r0, c1, r1), (width, height)), (x, y))
            x += width
        y += height
    return out


def smooth(image):
    return image.filter(ImageFilter.GaussianBlur(3))


def main():
    PICS.mkdir(exist_ok=True)
    wall, door, torch = frame('ftown1.fwl', 0), frame('ftown2.fwl', 0), frame('ftown1.fwl', 1)
    for name, image in (('native_wall', wall), ('native_door', door), ('native_torch', torch)):
        flat = Image.new('RGB', image.size, (60, 90, 140))
        flat.paste(image, (0, 0), image)
        enlarge(flat, 4).save(PICS / f'{name}.png')
    for name, sprite in (('native_hut', '052.obj'), ('native_well', '012.obj')):
        image = frame(sprite)
        flat = Image.new('RGB', image.size, (60, 90, 140))
        flat.paste(image, (0, 0), image)
        enlarge(flat, 6).save(PICS / f'{name}.png')

    plain = bay(wall)
    smooth(plain).save(PICS / 'guide_wall.png')

    # The door: the original's door bay (its door fills the panel), the door kept to about 80 percent of the bay's
    # height and plaster from the plain bay above it.
    door_bay = bay(door)
    guide = plain.copy()
    door_top = round(H * 0.2)
    lower = door_bay.crop((0, BEAM_PX, W, H - BEAM_PX)).resize((W, H - BEAM_PX - door_top), Image.LANCZOS)
    guide.paste(lower, (0, door_top))
    ImageDraw.Draw(guide).rectangle((POST_PX, door_top - 28, W - POST_PX, door_top), fill=(115, 73, 39))
    smooth(guide).save(PICS / 'guide_door.png')

    # The window (the original has none): a small casement in the upper middle of the panel, an oak frame and sill.
    guide = plain.copy()
    draw = ImageDraw.Draw(guide)
    left, right, top, bottom = 150, W - 150, 250, 560
    draw.rectangle((left - 24, top - 24, right + 24, bottom + 24), fill=(115, 73, 39))
    draw.rectangle((left, top, right, bottom), fill=(42, 46, 58))
    draw.rectangle((W // 2 - 8, top, W // 2 + 8, bottom), fill=(115, 73, 39))
    draw.rectangle((left - 40, bottom + 24, right + 40, bottom + 52), fill=(100, 62, 32))
    smooth(guide).save(PICS / 'guide_window.png')

    # The corner bay (post_left): a whole heavy post inside the left edge, twice the half post's width.
    guide = plain.copy()
    post = plain.crop((0, 0, POST_PX, H)).resize((POST_PX * 2 + 12, H), Image.LANCZOS)
    guide.paste(post, (0, 0))
    smooth(guide).save(PICS / 'guide_corner.png')
    print('wrote', sorted(p.name for p in PICS.glob('*.png')))


if __name__ == '__main__':
    main()
