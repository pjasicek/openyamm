#!/usr/bin/env python3
"""Portrait picker with a world filter (README.md), drawn over the party creation study's picker screenshot."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
FONTS = ROOT / 'level_generation/ui/menu_study_20260928/assets/fonts'
SHOT = ROOT / 'level_generation/ui/party_creation_study_20261101/shots/popup-portraits.png'
ICONS = ROOT / 'assets_dev/engine/icons_x2'
GOLD, IVORY, DIM = (201, 170, 106), (233, 212, 166), (160, 150, 128)

title = ImageFont.truetype(str(FONTS / 'Fondamento-Regular.ttf'), 28)
chip = ImageFont.truetype(str(FONTS / 'Fondamento-Regular.ttf'), 17)
small = ImageFont.truetype(str(FONTS / 'openyamm_lucida_faithful.ttf'), 13)
race_font = ImageFont.truetype(str(FONTS / 'Fondamento-Regular.ttf'), 24)

shot = Image.open(SHOT).convert('RGB')
image = shot.copy()
# Clear the header hint and the grid with the empty marble from the screenshot's lower right.
patch = shot.crop((760, 470, 1460, 820))
for col, x in enumerate(range(100, 1470, patch.width)):
    for row, y in enumerate(range(135, 830, patch.height)):
        tile = patch.transpose(Image.FLIP_LEFT_RIGHT) if col % 2 else patch
        tile = tile.transpose(Image.FLIP_TOP_BOTTOM) if row % 2 else tile
        image.paste(tile.crop((0, 0, min(patch.width, 1470 - x), min(patch.height, 830 - y))), (x, y))
band = shot.crop((760, 600, 1460, 640))
for x in range(535, 1400, band.width):
    image.paste(band.crop((0, 0, min(band.width, 1400 - x), 40)), (x, 78))
draw = ImageDraw.Draw(image)


def chips(x, y, labels, selected, label=None):
    if label:
        draw.text((x, y + 13), label, font=small, fill=DIM, anchor='lm')
        x += draw.textlength(label, font=small) + 10
    for text in labels:
        width = draw.textlength(text, font=chip) + 22
        on = text == selected
        draw.rectangle([x, y, x + width, y + 27], fill=(52, 46, 32) if on else (18, 24, 22),
                       outline=IVORY if on else (110, 98, 70), width=2 if on else 1)
        draw.text((x + width / 2, y + 14), text, font=chip, fill=IVORY if on else (196, 186, 160), anchor='mm')
        x += width + 8
    return x


# The existing All / Male / Female chips stay at the screenshot's place; the world chips follow them.
x = chips(548, 83, ['All worlds', 'Enroth', 'Antagarich', 'Jadame', 'Chedian'], 'Chedian', 'WORLD')
draw.text((x + 14, 97), 'MIGHT AND MAGIC IX PORTRAITS · LICHES ONCE OFFERED AT START', font=small, fill=DIM, anchor='lm')

RACES = [('Human', 'Learning +1', [1, 2, 3, 4]), ('Elf', 'Meditation +1', [5, 6, 7, 8]),
         ('Goblin', 'Disarm Traps +1 · MM9 half-orcs', [9, 10, 11, 12]), ('Dwarf', 'MM9 dwarves', [13, 14, 15, 16])]
symbol = ImageFont.truetype(str(FONTS / 'SourceSans3.ttf'), 15)
y = 136
for race, note, numbers in RACES:
    draw.text((114, y), race, font=race_font, fill=IVORY)
    draw.text((114 + draw.textlength(race, font=race_font) + 10, y + 14), note, font=small, fill=DIM, anchor='lm')
    for index, number in enumerate(numbers):
        px, py = 114 + index * 100, y + 34
        face = Image.open(ICONS / f'9pc{number:02d}-01.png').convert('RGBA')
        face.thumbnail((90, 114))
        card = Image.new('RGB', (92, 116), (14, 20, 18))
        card.paste(face, ((92 - face.width) // 2, 116 - face.height), face)
        image.paste(card, (px, py))
        selected = (race, index) == ('Human', 0)
        draw.rectangle([px - 1, py - 1, px + 92, py + 116], outline=IVORY if selected else GOLD,
                       width=3 if selected else 1)
        draw.text((px + 86, py + 108), f'#{9000 + number}', font=small, fill=IVORY, anchor='rb')
        draw.text((px + 14, py + 128), '\u2642' if number % 2 else '\u2640', font=symbol, fill=DIM, anchor='mm')
        draw.text((px + 52, py + 128), f'Voice {9000 + number}', font=small, fill=DIM, anchor='mm')
    y += 172
image.save(W / 'final' / 'portrait_picker_world_filter.png')
print('ok')
