#!/usr/bin/env python3
"""Xeen's Town Portal pages from the Codex paintings (README.md).

    python3 compose.py cloudside raw/tp_cloudside_vN.png
    python3 compose.py darkside raw/tp_darkside_vN.png
    python3 compose.py boxes          # final/boxes.yml from both faces' measured towns

Writes final/tp<face>.png (1280x960, the x2 of the 640x480 screen), final/tp<town>.png (the hover pictures: the
background under the town's box, a little brighter, with a crisp orange outline and a soft golden glow round the
miniature) and review/boxes_<face>.png.

As MM9's Chedian page (level_generation/ui/mm9_town_portal_20261108/compose.py): the painting's framed map is laid on
MM9's empty table (table_wood_v2.png) so that it ends at y 880 of 960, above the continent buttons and the Close
button (engine/ui/gameplay/town_portal.yml, from y 447 of 480); the destination label prints over the frame's lower
margin. Each town's box is its miniature's measured extent (TOWNS, canvas pixels, measured on the composed page) plus
ROOM units for the outline; the outline is an ellipse a little outside that extent.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W = Path(__file__).resolve().parent
TABLE = W.parents[2] / 'level_generation/ui/mm9_town_portal_20261108/raw/table_wood_v2.png'
CANVAS = (1280, 960)
FRAME_AT = (26, 8)
FRAME_HEIGHT = 872
SHADOW = 14
# room round a miniature's extent in its box, 640x480 units (the outline and its glow)
ROOM = 5

# Per face: the painting's frame (outer edge, painting pixels) and the six towns' miniatures (x0, y0, x1, y1 on the
# composed 1280x960 page), in town_portal.yml's order.
FACES = {
    'cloudside': {
        'frame': (154, 40, 1241, 912),
        'towns': {
            'Vertigo': (811, 572, 956, 652),
            'Rivercity': (630, 475, 826, 550),
            'Castle Burlock': (451, 236, 598, 338),
            'Winterkill': (210, 576, 333, 675),
            'Nightshadow': (420, 664, 560, 745),
            'Newcastle': (455, 562, 598, 640),
        },
    },
    'darkside': {
        'frame': (154, 40, 1241, 912),
        'towns': {
            'Castleview': (165, 507, 340, 596),
            'Castle Kalindra': (180, 624, 250, 692),
            'Sandcaster': (760, 445, 918, 540),
            'Lakeside': (775, 337, 882, 395),
            'Necropolis': (252, 282, 400, 380),
            'Olympus': (665, 117, 825, 182),
        },
    },
}


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - size[0]) // 2, (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def page(painting: Image.Image, frame: tuple[int, int, int, int]) -> Image.Image:
    wood = cover(Image.open(TABLE).convert('RGB'), CANVAS)
    scale = FRAME_HEIGHT / (frame[3] - frame[1])
    box = (frame[0] - SHADOW, frame[1] - SHADOW, frame[2] + SHADOW, frame[3] + SHADOW)
    cut = painting.crop(box)
    size = (round(cut.width * scale), round(cut.height * scale))
    cut = cut.resize(size, Image.LANCZOS)
    margin = round(SHADOW * scale)
    inner = Image.new('L', size, 0)
    ImageDraw.Draw(inner).rectangle((margin, margin, size[0] - margin - 1, size[1] - margin - 1), fill=255)
    mask = inner.filter(ImageFilter.GaussianBlur(margin * 0.45))
    mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(inner)))
    at = (FRAME_AT[0] - margin, FRAME_AT[1] - margin)
    shadow = Image.new('L', CANVAS, 0)
    ImageDraw.Draw(shadow).rectangle((at[0] + margin + 6, at[1] + margin + 8, at[0] + size[0] - margin + 6,
                                      at[1] + size[1] - margin + 8), fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.composite(Image.new('RGB', CANVAS, (12, 7, 3)), wood, shadow)
    canvas.paste(cut, at, mask)
    return canvas


def town_box(extent: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """The hover box in 640x480 units: the miniature's extent plus ROOM units."""
    x0, y0, x1, y1 = extent
    ix, iy = int(np.floor(x0 / 2)) - ROOM, int(np.floor(y0 / 2)) - ROOM
    return ix, iy, int(np.ceil(x1 / 2)) + ROOM - ix, int(np.ceil(y1 / 2)) + ROOM - iy


def hover(canvas: Image.Image, extent: tuple[int, int, int, int]) -> tuple[Image.Image, tuple[int, int, int, int]]:
    ix, iy, iw, ih = town_box(extent)
    origin = (ix * 2, iy * 2)
    crop = canvas.crop((origin[0], origin[1], origin[0] + iw * 2, origin[1] + ih * 2))
    # an ellipse a little outside the extent's edges (the miniatures are round-ish, their corners empty), a crisp
    # 3-pixel stroke drawn supersampled, and a soft glow just outside it that fades out before the box's edge
    cx, cy = (extent[0] + extent[2]) / 2 - origin[0], (extent[1] + extent[3]) / 2 - origin[1]
    rx, ry = (extent[2] - extent[0]) / 2 * 1.06 + 3, (extent[3] - extent[1]) / 2 * 1.06 + 3
    ss = 4
    big = Image.new('L', (crop.width * ss, crop.height * ss), 0)
    ImageDraw.Draw(big).ellipse(((cx - rx) * ss, (cy - ry) * ss, (cx + rx) * ss, (cy + ry) * ss), outline=255,
                                width=3 * ss)
    stroke = big.resize(crop.size, Image.LANCZOS)
    inside = Image.new('L', crop.size, 0)
    ImageDraw.Draw(inside).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    ring = Image.new('L', crop.size, 0)
    ImageDraw.Draw(ring).ellipse((cx - rx - 6, cy - ry - 6, cx + rx + 6, cy + ry + 6), fill=255)
    glow = np.clip(np.asarray(ring).astype(float) - np.asarray(inside), 0, 255)
    glow = np.asarray(Image.fromarray(glow.astype('uint8')).filter(ImageFilter.GaussianBlur(3))).astype(float)
    ys, xs = np.mgrid[0:crop.height, 0:crop.width]
    edge = np.minimum.reduce([xs, ys, crop.width - 1 - xs, crop.height - 1 - ys]).astype(float)
    glow *= np.clip(edge / 4, 0, 1) * 0.6
    glow = Image.fromarray(np.clip(glow, 0, 255).astype('uint8'))
    lit = ImageEnhance.Brightness(crop).enhance(1.08)
    lit = Image.composite(Image.new('RGB', crop.size, (255, 196, 90)), lit, glow)
    lit = Image.composite(Image.new('RGB', crop.size, (255, 142, 24)), lit, stroke)
    return lit, (ix, iy, iw, ih)


def name_of(town: str) -> str:
    return 'tp' + town.lower().replace(' ', '')


def compose(face: str, painting_path: str) -> None:
    spec = FACES[face]
    canvas = page(Image.open(W / painting_path).convert('RGB'), spec['frame'])
    canvas.save(W / f'final/tp{face}.png')
    review = canvas.copy()
    draw = ImageDraw.Draw(review)
    for town, extent in spec['towns'].items():
        picture, (ix, iy, iw, ih) = hover(canvas, extent)
        picture.save(W / f'final/{name_of(town)}.png')
        review.paste(picture, (ix * 2, iy * 2))
        draw.rectangle((ix * 2, iy * 2, (ix + iw) * 2 - 1, (iy + ih) * 2 - 1), outline=(255, 0, 255), width=2)
        print(f'{town}: {name_of(town)} {ix} {iy} {iw} {ih}')
    # the destination label and the Close button (town_portal.yml)
    draw.rectangle((680, 804, 1160, 860), outline=(0, 255, 255), width=2)
    draw.rectangle((1108, 894, 1274, 954), outline=(0, 255, 255), width=2)
    review.save(W / f'review/boxes_{face}.png')


def overlaps() -> list[str]:
    found = []
    for face, spec in FACES.items():
        named = [(town, town_box(extent)) for town, extent in spec['towns'].items()]
        for i, (a, (ax, ay, aw, ah)) in enumerate(named):
            for b, (bx, by, bw, bh) in named[i + 1:]:
                if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                    found.append(f'{face}: {a} and {b} overlap')
    return found


def boxes() -> None:
    problems = overlaps()
    if problems:
        raise SystemExit('\n'.join(problems))
    lines = ['# Xeen Town Portal hover pictures and boxes, 640x480 units (compose.py).']
    for face, spec in FACES.items():
        lines.append(f'# {face}')
        for town, extent in spec['towns'].items():
            ix, iy, iw, ih = town_box(extent)
            lines.append(f'{town}: {{name: {name_of(town)}, x: {ix}, y: {iy}, w: {iw}, h: {ih}}}')
    (W / 'final/boxes.yml').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    if sys.argv[1] == 'boxes':
        boxes()
    else:
        compose(sys.argv[1], sys.argv[2])
