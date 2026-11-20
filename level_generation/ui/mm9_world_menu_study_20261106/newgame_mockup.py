#!/usr/bin/env python3
"""Choose Starting Continent with four worlds (README.md), drawn over the approved menu study's capture."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
FONTS = ROOT / 'level_generation/ui/menu_study_20260928/assets/fonts'
SHOT = ROOT / 'level_generation/ui/menu_study_20260928/previews/r03-worlds.png'
GLOBES = ROOT / 'assets_dev/engine/hud_x2/menus'
IVORY, DIM, GOLD = (233, 212, 166), (194, 182, 155), (150, 128, 84)
CARDS = [('enroth', 'Enroth', 'MIGHT AND MAGIC VI', 'BEGIN IN NEW SORPIGAL'),
         ('antagarich', 'Antagarich', 'MIGHT AND MAGIC VII', 'BEGIN IN EMERALD ISLAND'),
         ('jadame', 'Jadame', 'MIGHT AND MAGIC VIII', 'BEGIN IN DAGGER WOUND ISLANDS'),
         ('chedian', 'Chedian', 'MIGHT AND MAGIC IX', 'BEGIN ON THE ISLE OF ASHES')]

name_font = ImageFont.truetype(str(FONTS / 'Fondamento-Regular.ttf'), 36)
caps = ImageFont.truetype(str(FONTS / 'openyamm_lucida_faithful.ttf'), 14)
tiny = ImageFont.truetype(str(FONTS / 'openyamm_lucida_faithful.ttf'), 12)

shot = Image.open(SHOT).convert('RGB')
image = shot.copy()
gap = shot.crop((579, 257, 596, 739))
for index, x in enumerate(range(166, 1436, gap.width)):
    tile = gap.transpose(Image.FLIP_LEFT_RIGHT) if index % 2 else gap
    image.paste(tile.crop((0, 0, min(gap.width, 1436 - x), gap.height)), (x, 257))
fill = shot.crop((606, 262, 996, 292))
draw = ImageDraw.Draw(image)


def spaced(x, y, text, font, color, spacing=3):
    width = sum(draw.textlength(c, font=font) + spacing for c in text) - spacing
    cursor = x - width / 2
    for c in text:
        draw.text((cursor, y), c, font=font, fill=color, anchor='lm')
        cursor += draw.textlength(c, font=font) + spacing
    return width


width, step, top, bottom = 302, 318, 257, 738
for index, (key, name, game, start) in enumerate(CARDS):
    x0 = 172 + index * step
    selected = key == 'chedian'
    for row, y in enumerate(range(top, bottom, fill.height)):
        tile = fill.transpose(Image.FLIP_TOP_BOTTOM) if row % 2 else fill
        image.paste(tile.crop((0, 0, width, min(fill.height, bottom - y))), (x0, y))
    if selected:
        draw.rectangle([x0, top, x0 + width, bottom], fill=None, outline=(222, 196, 140), width=2)
        spaced(x0 + width - 52, top + 24, 'SELECTED', tiny, DIM, 2)
    else:
        draw.rectangle([x0, top, x0 + width, bottom], outline=GOLD, width=1)
    globe = Image.open(W / 'final' / 'omenu_continent_chedian.png' if key == 'chedian'
                       else GLOBES / f'omenu_continent_{key}.png').convert('RGB').resize((236, 236), Image.LANCZOS)
    mask = Image.new('L', (236 * 4, 236 * 4), 0)
    ImageDraw.Draw(mask).ellipse([6, 6, 236 * 4 - 6, 236 * 4 - 6], fill=255)
    image.paste(globe, (x0 + (width - 236) // 2, top + 52), mask.resize((236, 236), Image.LANCZOS))
    cx = x0 + width / 2
    spaced(cx, 594, game, caps, DIM, 3)
    draw.text((cx, 641), name, font=name_font, fill=IVORY, anchor='mm')
    box_width = spaced(cx, 704, start, tiny, DIM, 2) + 18
    draw.rectangle([cx - box_width / 2, 692, cx + box_width / 2, 716], outline=GOLD, width=1)
image.save(W / 'final' / 'new_game_four_worlds.png')
print('ok')
