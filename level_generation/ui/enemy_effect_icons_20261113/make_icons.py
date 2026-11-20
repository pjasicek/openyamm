#!/usr/bin/env python3
"""Effect icons for the enemy health bars: glyph-free clips of the restored spellbook art, 128x128 RGBA.

The same recipe as the Obsidian party buff icons (obsidian_overlays_20260928/prepare_assets.py and
staging/export_graphics.mjs): a polygon in percent of the source keeps the spell's runes out, the clip is cropped
to its artwork (alpha above 28) with 4 px of padding and fitted, centred, into 128x128. Source pixels are not
changed. Writes assets_source/engine/icons_x2/<name>.png (cook with tools/cook_ui_textures.py) and preview.png here.

  python3 level_generation/ui/enemy_effect_icons_20261113/make_icons.py [--preview-only]
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

REPO = Path(__file__).resolve().parents[3]
ICONS = REPO / 'assets_dev/engine/icons_x2'
OUT = REPO / 'assets_source/engine/icons_x2'
HERE = Path(__file__).resolve().parent
SIZE = 128

# name: (spellbook icon, clip polygon in percent of the source).
ICONS_TO_MAKE = {
    'obsidian_debuff_stun': ('sbe01a', [(27, 0), (100, 0), (100, 70), (57, 70), (57, 100), (0, 100), (0, 28),
                                        (27, 28)]),
    'obsidian_debuff_paralyze': ('sbl04a', [(45, 0), (100, 0), (100, 100), (0, 100), (0, 27), (45, 27)]),
    'obsidian_debuff_slow': ('sbe02a', [(0, 0), (100, 0), (100, 61), (0, 61)]),
    'obsidian_debuff_fear': ('sbm08a', [(0, 0), (100, 0), (100, 18), (61, 18), (61, 100), (0, 100)]),
    'obsidian_debuff_charm': ('sbm05a', [(0, 0), (100, 0), (100, 72), (0, 72)]),
    'obsidian_debuff_berserk': ('sbm07a', [(0, 0), (100, 0), (100, 70), (20, 70), (20, 54), (0, 54)]),
    'obsidian_debuff_enslave': ('sbm11a', [(43, 0), (100, 0), (100, 100), (0, 100), (0, 48), (43, 48)]),
    'obsidian_debuff_control_undead': ('sbdk06a', [(0, 36), (100, 36), (100, 100), (0, 100)]),
    'obsidian_debuff_shrink': ('sbdk04a', [(0, 0), (100, 0), (100, 72), (80, 72), (80, 86), (0, 86)]),
    'obsidian_debuff_dark_grasp': ('sbdk08a', [(0, 0), (100, 0), (100, 90), (82, 90), (82, 76), (28, 76),
                                               (28, 58), (0, 58)]),
    'obsidian_buff_sbs02a': ('sbs02a', [(36, 0), (100, 0), (100, 100), (0, 100), (0, 32), (36, 32)]),
    'obsidian_buff_sbs03a': ('sbs03a', [(0, 0), (100, 0), (100, 64), (0, 64)]),
    'obsidian_buff_sbl08a': ('sbl08a', [(0, 0), (100, 0), (100, 68), (0, 68)]),
    'obsidian_buff_sbl09a': ('sbl09a', [(0, 14), (75, 14), (75, 40), (100, 40), (100, 100), (0, 100)]),
    'obsidian_buff_sbb07a': ('sbb07a', [(38, 0), (100, 0), (100, 100), (46, 100), (46, 28), (38, 28)]),
    'obsidian_buff_sbdk07a': ('sbdk07a', [(0, 26), (100, 26), (100, 100), (0, 100)]),
}


def make(source_name, polygon):
    image = Image.open(ICONS / (source_name + '.png')).convert('RGBA')
    w, h = image.size
    mask = Image.new('L', image.size, 255 if polygon is None else 0)
    if polygon is not None:
        ImageDraw.Draw(mask).polygon([(x * w / 100, y * h / 100) for x, y in polygon], fill=255)
    alpha = ImageChops.multiply(image.getchannel('A'), mask)
    x1, y1, x2, y2 = alpha.point(lambda a: 255 if a > 28 else 0).getbbox()
    clipped = image.copy()
    clipped.putalpha(alpha)
    pad = 4
    box = (x1 - pad, y1 - pad, x2 + pad, y2 + pad)
    side = max(box[2] - box[0], box[3] - box[1])
    # Centre the crop in a square, as preserveAspectRatio="xMidYMid meet" does.
    square = Image.new('RGBA', (side, side))
    square.paste(clipped.crop(box), ((side - (box[2] - box[0])) // 2, (side - (box[3] - box[1])) // 2))
    return square.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    preview_only = '--preview-only' in sys.argv
    sheet = Image.new('RGBA', (len(ICONS_TO_MAKE) * (SIZE + 8) + 8, 3 * SIZE + 32), (36, 34, 40, 255))
    for index, (name, (source, polygon)) in enumerate(ICONS_TO_MAKE.items()):
        icon = make(source, polygon)
        if not preview_only:
            icon.save(OUT / (name + '.png'))
        x = 8 + index * (SIZE + 8)
        sheet.alpha_composite(icon, (x, 8))
        # How it reads at bar size (16 px) and at 2x that.
        for row, px in ((1, 32), (2, 16)):
            small = icon.resize((px, px), Image.LANCZOS)
            sheet.alpha_composite(small, (x + (SIZE - px) // 2, 8 + row * SIZE + (SIZE - px) // 2))
    sheet.save(HERE / 'preview.png')
    print(f'{len(ICONS_TO_MAKE)} icons' + ('' if preview_only else f' written to {OUT}'))


if __name__ == '__main__':
    main()
