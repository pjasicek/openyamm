#!/usr/bin/env python3
"""Reference pictures of the classic stone kit (2026-11-24) from Clouds of Xeen's castle walls (XEEN.CC fcstl1/fcstl2,
the nearest front wall, 168 x 85: two marbled sandstone slabs between columns of dressed quoins, a course of blocks
along the top and the bottom, the slabs meeting in a joint at the middle).

Writes pics/<name>.png, named in specs.yml as `pic/<name>`:
- native_cwall, native_cdoor: the plain wall (fcstl1 frame 0) and the arched iron-banded door (fcstl2 frame 0),
  enlarged 4x with nearest neighbour.
- guide_swall: one slab bay (the left slab, from the quoins' inner edge to the middle joint) at 512 x 1024.
- guide_sdoor: the door's slab, the arched door in its middle, at 512 x 1024.
- guide_swin: the slab bay with a narrow arched window drawn in its upper middle (the original has none).
- guide_quoin: the left column of quoins, tiled twice upward; guide_course: the top course, tiled twice across.
All guides smoothed so the model takes the layout and the colours, not the pixels.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SPRITES = HERE.parents[3] / 'reference/mm4_5_world_of_xeen/unpacked/sprites/xeen'
PICS = HERE / 'pics'
W, H = 512, 1024
# Measured on fcstl1 frame 0 (mortar lines): quoins at 0-8 and 159-167, courses at rows 0-8 and 76-84, the slabs'
# joint at 83; the door's arch on fcstl2 frame 0 spans 49-117.
SLAB = (9, 83)
DOOR_SLAB = (46, 121)


def frame(name, index):
    return Image.open(SPRITES / name / f'frame_{index:04d}.png').convert('RGB')


def smooth(image):
    return image.filter(ImageFilter.GaussianBlur(3))


def main():
    PICS.mkdir(exist_ok=True)
    wall, door = frame('fcstl1.fwl', 0), frame('fcstl2.fwl', 0)
    wall.resize((wall.width * 4, wall.height * 4), Image.NEAREST).save(PICS / 'native_cwall.png')
    door.resize((door.width * 4, door.height * 4), Image.NEAREST).save(PICS / 'native_cdoor.png')

    slab = wall.crop((SLAB[0], 0, SLAB[1], wall.height)).resize((W, H), Image.LANCZOS)
    smooth(slab).save(PICS / 'guide_swall.png')
    smooth(door.crop((DOOR_SLAB[0], 0, DOOR_SLAB[1], door.height)).resize((W, H), Image.LANCZOS)).save(
        PICS / 'guide_sdoor.png')

    # The window: a narrow round-headed opening ringed by voussoirs, in the slab's upper middle.
    guide = slab.copy()
    draw = ImageDraw.Draw(guide)
    stone, glass = (176, 112, 70), (40, 44, 52)
    left, right, top, bottom = 170, W - 170, 250, 600
    draw.rectangle((left - 30, top + 86, right + 30, bottom + 30), fill=stone)
    draw.pieslice((left - 30, top - 30, right + 30, top + 2 * 86 + 30), 180, 360, fill=stone)
    draw.rectangle((left, top + 86, right, bottom), fill=glass)
    draw.pieslice((left, top, right, top + 2 * 86), 180, 360, fill=glass)
    draw.rectangle((left - 46, bottom + 30, right + 46, bottom + 58), fill=stone)
    smooth(guide).save(PICS / 'guide_swin.png')

    quoin = wall.crop((0, 0, SLAB[0], wall.height))
    column = Image.new('RGB', (quoin.width, quoin.height * 2))
    column.paste(quoin, (0, 0))
    column.paste(quoin, (0, quoin.height))
    smooth(column.resize((256, 256 * column.height // column.width // 4), Image.LANCZOS)).save(
        PICS / 'guide_quoin.png')
    course = wall.crop((0, 0, wall.width, 9))
    band = Image.new('RGB', (course.width * 2, course.height))
    band.paste(course, (0, 0))
    band.paste(course, (course.width, 0))
    smooth(band.resize((1024, 1024 * band.height // band.width), Image.LANCZOS)).save(PICS / 'guide_course.png')
    print('wrote', sorted(p.name for p in PICS.glob('guide_s*.png')) + ['guide_quoin.png', 'guide_course.png'])


if __name__ == '__main__':
    main()
