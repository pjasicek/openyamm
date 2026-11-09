#!/usr/bin/env python3
"""Exports the study's 128 x 128 runtime candidates and builds the preview images of index.html.

Sizes follow the engine at 1600 x 900 (design scale 900 / 480 = 1.875): 28 design units in the Choose Class grid
(MenuDesignScreen::drawConfirmation), 34 beside the selected portrait (CharacterCreationClassEmblem) and 20 above
each party slot (NewGameScreen). The mockups are composites over the 2026-10-06 native captures, not game captures.
"""

import glob
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

STUDY = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
REPO = os.path.normpath(os.path.join(STUDY, '../../..'))
EXISTING = os.path.join(REPO, 'assets_dev/engine/hud_x2/menus/classes')
CAPTURES = os.path.join(REPO, 'output/screenshots/class_icons_simple_20261006')
FONT = os.path.join(REPO, 'assets_dev/engine/fonts/truetype/fondamento_regular.ttf')
PREVIEWS = os.path.join(STUDY, 'previews')
SCALE = 900 / 480
STONE = (22, 30, 27, 255)


def export_runtime(classes):
    for entry in classes:
        master = os.path.join(STUDY, 'masters', entry['file'])
        if not os.path.exists(master):
            continue
        # The existing sixteen fill about 116 of 128 pixels on their longer side (median); centre to match.
        image = Image.open(master).convert('RGBA')
        image = image.crop(image.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox())
        fit = 116 / max(image.size)
        image = image.resize((round(image.width * fit), round(image.height * fit)), Image.LANCZOS)
        runtime = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        runtime.alpha_composite(image, ((128 - image.width) // 2, (128 - image.height) // 2))
        runtime.save(os.path.join(STUDY, 'runtime_x2', entry['file']))


def icon(path, size):
    return Image.open(path).convert('RGBA').resize((size, size), Image.LANCZOS)


def size_sheet(classes):
    """Every class icon, old and new, at the three in-game sizes on the dark stone colour."""
    existing = sorted(glob.glob(os.path.join(EXISTING, '*.png')))
    new = [os.path.join(STUDY, 'runtime_x2', e['file']) for e in classes]
    new = [p for p in new if os.path.exists(p)]
    sizes = [round(34 * SCALE), round(28 * SCALE), round(20 * SCALE)]
    cell = sizes[0] + 12
    paths = existing + new
    sheet = Image.new('RGBA', (len(paths) * cell + 24, sum(s + 12 for s in sizes) + 24), STONE)
    draw = ImageDraw.Draw(sheet)
    x0 = 12 + len(existing) * cell - 6
    draw.line([(x0, 6), (x0, sheet.height - 6)], fill=(200, 170, 90, 255), width=2)
    for i, path in enumerate(paths):
        y = 12
        for size in sizes:
            sheet.alpha_composite(icon(path, size), (12 + i * cell + (cell - 12 - size) // 2, y))
            y += size + 12
    sheet.save(os.path.join(PREVIEWS, 'sizes_in_game.png'))


def cover(image, box, source_dx):
    """Paints a box over with the stone a fixed distance to its right."""
    x, y, w, h = box
    image.paste(image.crop((x + source_dx, y, x + source_dx + w, y + h)), (x, y))


def grid_mockup(classes):
    """The first two rows of the Human Choose Class grid with the four new classes in place of the old ones."""
    shot = Image.open(os.path.join(CAPTURES, 'human-class-grid.png')).convert('RGBA')
    font = ImageFont.truetype(FONT, round(13.8667 * SCALE * 1.06))
    draw = ImageDraw.Draw(shot)
    # Button rects measured on the capture: two columns at x 305 and 811, rows 46 design units apart.
    buttons = [(305, 266), (811, 266), (305, 352), (811, 352)]
    size = round(28 * SCALE)
    for (bx, by), entry in zip(buttons, classes):
        path = os.path.join(STUDY, 'runtime_x2', entry['file'])
        if not os.path.exists(path):
            continue
        cover(shot, (bx + 12, by + 4, 250, 63), 190)
        shot.alpha_composite(icon(path, size), (bx + round(8 * SCALE), by + (71 - size) // 2))
        draw.text((bx + round(44 * SCALE), by + 35), entry['class'], font=font, fill=(0xe8, 0xd1, 0xa4, 255),
                  anchor='lm')
    shot.crop((262, 60, 1338, 450)).save(os.path.join(PREVIEWS, 'mockup_class_grid.png'))


def emblem_mockup(classes):
    """The selected-portrait emblem of the creation screen for each new class."""
    shot = Image.open(os.path.join(CAPTURES, 'knight-party.png')).convert('RGBA')
    size = round(34 * SCALE)
    ex, ey = round(134 * SCALE), round(154 * SCALE)
    old = icon(os.path.join(EXISTING, 'knight.png'), size)
    mask = old.getchannel('A').point(lambda a: 255 if a > 8 else 0).filter(ImageFilter.MaxFilter(7))
    tiles = []
    for entry in classes:
        path = os.path.join(STUDY, 'runtime_x2', entry['file'])
        if not os.path.exists(path):
            continue
        frame = shot.copy()
        patch = frame.crop((ex + 80, ey, ex + 80 + size, ey + size))
        frame.paste(patch, (ex, ey), mask)
        frame.alpha_composite(icon(path, size), (ex, ey))
        tiles.append(frame.crop((50, 130, 330, 370)))
    if tiles:
        strip = Image.new('RGBA', (len(tiles) * 288 - 8, 240), STONE)
        for i, tile in enumerate(tiles):
            strip.paste(tile, (i * 288, 0))
        strip.save(os.path.join(PREVIEWS, 'mockup_portrait_emblem.png'))


def main():
    with open(os.path.join(STUDY, 'classes.json')) as f:
        classes = json.load(f)
    os.makedirs(PREVIEWS, exist_ok=True)
    export_runtime(classes)
    size_sheet(classes)
    grid_mockup(classes)
    emblem_mockup(classes)


if __name__ == '__main__':
    main()
