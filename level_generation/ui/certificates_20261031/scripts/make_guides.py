"""Draws the layout guides the Codex certificate paintings follow (1536 x 1024): the frame band, the seal recess and
the zones that stay clear for the text the game draws. The engine's WinGameScreen uses the same numbers.
Usage: python3 -I make_guides.py"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH, HEIGHT = 1536, 1024
FRAME = 64
SEAL = (768, 132, 70)
# Text zones: the continent certificates' and the grand one's, which keeps a band of three medallions below.
TEXT_CONTINENT = (330, 230, 1206, 900)
TEXT_GRAND = (330, 230, 1206, 790)
MEDALLIONS = [(548, 880, 74), (768, 880, 74), (988, 880, 74)]


def guide(grand):
    image = Image.new('RGB', (WIDTH, HEIGHT), (24, 32, 30))
    draw = ImageDraw.Draw(image)
    draw.rectangle((FRAME, FRAME, WIDTH - FRAME, HEIGHT - FRAME), fill=(226, 212, 178))
    text = TEXT_GRAND if grand else TEXT_CONTINENT
    draw.rectangle(text, outline=(200, 30, 30), width=6)
    draw.text((text[0] + 16, text[1] + 12), 'TEXT ZONE: keep plain parchment, very faint at most', fill=(200, 30, 30))
    x, y, r = SEAL
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(20, 26, 26), outline=(40, 60, 210), width=6)
    draw.text((x - 52, y - 6), 'SEAL RECESS (empty)', fill=(120, 150, 255))
    if grand:
        for x, y, r in MEDALLIONS:
            draw.ellipse((x - r, y - r, x + r, y + r), outline=(20, 150, 60), width=6)
            draw.text((x - 40, y - 6), 'CONTINENT', fill=(20, 120, 40))
    else:
        for box in ((FRAME + 14, 560, 316, HEIGHT - FRAME - 14), (1220, 560, WIDTH - FRAME - 14, HEIGHT - FRAME - 14)):
            draw.rectangle(box, outline=(20, 150, 60), width=6)
            draw.text((box[0] + 12, box[1] + 12), 'VIGNETTE', fill=(20, 120, 40))
    draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), outline=(40, 60, 210), width=4)
    draw.text((12, HEIGHT // 2), 'FRAME', fill=(120, 150, 255))
    return image


for name, grand in (('guide_continent.png', False), ('guide_grand.png', True)):
    guide(grand).save(os.path.join(HERE, name))
    print('wrote', name)
