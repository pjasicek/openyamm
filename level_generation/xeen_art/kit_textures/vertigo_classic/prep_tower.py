#!/usr/bin/env python3
"""Reference pictures of the classic tower kit (2026-11-24) from Clouds of Xeen's tower walls (XEEN.CC ftowr1/ftowr2,
the nearest front wall, 168 x 85: three courses of big dark grey blocks; the door of dark planks under a rounded
head with an iron ring, between stone pilasters under a lintel).

Writes pics/<name>.png, named in specs.yml as `pic/<name>`:
- native_twall, native_tdoor: the plain wall (ftowr1 frame 0) and the door (ftowr2 frame 0), enlarged 4x.
- guide_twall: the wall tiled 2 x 2, smoothed (the tile's material and scale: three courses to a wall's height).
- guide_tdoor: the door with its pilasters and some wall either side, at the bay's 1:2, smoothed.
- guide_twin: the wall with a narrow barred window drawn in (the original has none).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SPRITES = HERE.parents[3] / 'reference/mm4_5_world_of_xeen/unpacked/sprites/xeen'
PICS = HERE / 'pics'
W, H = 512, 1024
DOOR_BAY = (36, 129)      # the door and its pilasters (44-121, measured) with a little wall either side


def frame(name, index):
    return Image.open(SPRITES / name / f'frame_{index:04d}.png').convert('RGB')


def smooth(image):
    return image.filter(ImageFilter.GaussianBlur(3))


def main():
    PICS.mkdir(exist_ok=True)
    wall, door = frame('ftowr1.fwl', 0), frame('ftowr2.fwl', 0)
    wall.resize((wall.width * 4, wall.height * 4), Image.NEAREST).save(PICS / 'native_twall.png')
    door.resize((door.width * 4, door.height * 4), Image.NEAREST).save(PICS / 'native_tdoor.png')
    tiled = Image.new('RGB', (wall.width * 2, wall.height * 2))
    for dx in (0, 1):
        for dy in (0, 1):
            tiled.paste(wall, (dx * wall.width, dy * wall.height))
    smooth(tiled.resize((1024, 1024 * tiled.height // tiled.width), Image.LANCZOS)).save(PICS / 'guide_twall.png')
    smooth(door.crop((DOOR_BAY[0], 0, DOOR_BAY[1], door.height)).resize((W, H), Image.LANCZOS)).save(
        PICS / 'guide_tdoor.png')
    # The window: a narrow slit with a rounded head and iron bars, a stone sill, on the wall's blocks at the bay's 1:2.
    guide = wall.crop((40, 0, 83, 85)).resize((W, H), Image.LANCZOS)
    draw = ImageDraw.Draw(guide)
    stone, dark, iron = (70, 70, 72), (12, 12, 14), (95, 95, 100)
    left, right, top, bottom = 196, W - 196, 260, 620
    draw.rectangle((left - 26, top + 60, right + 26, bottom + 26), fill=stone)
    draw.pieslice((left - 26, top - 26, right + 26, top + 120 + 26), 180, 360, fill=stone)
    draw.rectangle((left, top + 60, right, bottom), fill=dark)
    draw.pieslice((left, top, right, top + 120), 180, 360, fill=dark)
    for x in (W // 2 - 30, W // 2, W // 2 + 30):
        draw.rectangle((x - 5, top + 20, x + 5, bottom), fill=iron)
    draw.rectangle((left - 40, bottom + 26, right + 40, bottom + 54), fill=stone)
    smooth(guide).save(PICS / 'guide_twin.png')
    print('wrote', ['native_twall', 'native_tdoor', 'guide_twall', 'guide_tdoor', 'guide_twin'])


if __name__ == '__main__':
    main()
