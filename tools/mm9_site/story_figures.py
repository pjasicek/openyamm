#!/usr/bin/env python3
"""Annotated figures for the story walkthrough (story/*.yml `figures`), written to tools/mm9_site/story/img/.

    python3 tools/mm9_site/story_figures.py        # needs output/mm9_site (run build_site.py once) for the map image

darkpassageway_mirrors.webp: the desert of the Dark Passageway from above on the guide's own map image, with the
gemstone, the four mirrors (their order, angle and clicks from 0), the light's path and the crystal it must reach.
Positions are the rebuilt map's (worlds/mm9/events/maps/darkpassageway.lua MIRRORS, props.json); the angles are
PassageMirror.scr's targets. The in-game capture beside it (darkpassageway_mirrors_light.webp) is made by hand: a save
with the mirrors set, a screenshot tour whose first shot runs `event 215` (the tour pauses the world, so the beams stay),
cropped to the view.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "output/mm9_site"
OUT = Path(__file__).resolve().parent / "story/img"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Native positions (x east, y north)
GEMSTONE = (-3272, -13102)
RECEIVER = (-5734, -6190)              # BeamReceiver1, the crystal the light must reach
MIRRORS = [                            # in the order the light reaches them: (position, angle, clicks from 0)
    ((-6548, -13107), 330, 33),
    ((-3113, -11141), 10, 1),
    ((-6881, -10486), 340, 34),
    ((-3031, -9134), 50, 5),
]
VIEW = (-7900, -2300, -14100, -5300)   # x min, x max, y min, y max of the figure
SCALE = 0.16                           # pixels per unit


def map_presentation(map_id: str) -> dict:
    text = (SITE / "data/guide.js").read_text()
    start = text.index(f'"id":"{map_id}"')
    bounds = json.loads(re.search(r'"bounds":(\[[^\]]*\])', text[start:]).group(1))
    return {"bounds": bounds, "flipV": '"flipV":true' in text[start:start + 400]}


def darkpassageway_mirrors() -> Path:
    presentation = map_presentation("darkpassageway")
    min_x, max_x, min_y, max_y = presentation["bounds"]
    source = Image.open(SITE / "img/maps/darkpassageway.webp").convert("RGB")
    sw, sh = source.size

    def source_px(x, y):
        return (x - min_x) / (max_x - min_x) * sw, (max_y - y) / (max_y - min_y) * sh

    x0, x1, y0, y1 = VIEW
    width, height = int((x1 - x0) * SCALE), int((y1 - y0) * SCALE)
    left, top = source_px(x0, y1)
    right, bottom = source_px(x1, y0)
    image = source.crop((int(left), int(top), int(right), int(bottom))).resize((width, height), Image.LANCZOS)
    draw = ImageDraw.Draw(image, "RGBA")

    def px(point):
        return (point[0] - x0) * SCALE, (y1 - point[1]) * SCALE

    font = ImageFont.truetype(FONT, 22)
    small = ImageFont.truetype(FONT, 18)
    bold = ImageFont.truetype(FONT_BOLD, 26)
    title = ImageFont.truetype(FONT_BOLD, 28)

    # the light's path, gemstone -> mirrors -> crystal, with an arrowhead on each leg
    path = [GEMSTONE] + [m[0] for m in MIRRORS] + [RECEIVER]
    for a, b in zip(path, path[1:]):
        pa, pb = px(a), px(b)
        draw.line([pa, pb], fill=(255, 214, 40, 255), width=6)
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        length = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / length, dy / length
        tip = (pa[0] + dx * 0.55, pa[1] + dy * 0.55)
        draw.polygon([(tip[0] + ux * 18, tip[1] + uy * 18), (tip[0] - uy * 11, tip[1] + ux * 11),
                      (tip[0] + uy * 11, tip[1] - ux * 11)], fill=(255, 214, 40, 255))

    def badge(center, text_font, label, fill):
        cx, cy = center
        draw.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=fill, outline=(20, 15, 10, 255), width=3)
        draw.text((cx, cy), label, font=text_font, fill=(255, 255, 255, 255), anchor="mm")

    def note(anchor, lines, side):
        """A label box beside a marker (side: left, right, above, below), kept inside the figure."""
        x, y = anchor
        boxes = [draw.textbbox((0, 0), line, font=f) for line, f in lines]
        w = max(b[2] - b[0] for b in boxes) + 20
        h = sum(b[3] - b[1] + 8 for b in boxes) + 12
        bx = {"right": x + 34, "left": x - 34 - w}.get(side, x - w / 2)
        by = {"above": y - 34 - h, "below": y + 34}.get(side, y - h / 2)
        bx = min(max(bx, 10), width - w - 10)
        draw.rounded_rectangle([bx, by, bx + w, by + h], radius=8, fill=(25, 20, 14, 215))
        cursor = by + 8
        for (line, f), b in zip(lines, boxes):
            draw.text((bx + 10, cursor), line, font=f, fill=(255, 240, 210, 255))
            cursor += b[3] - b[1] + 8

    order = ["1st", "2nd", "3rd", "4th"]
    sides = ["below", "below", "below", "below"]     # clear of the light's path
    for k, (pos, angle, clicks) in enumerate(MIRRORS):
        p = px(pos)
        badge(p, bold, str(k + 1), (176, 40, 30, 255))
        clicks_text = f"{clicks} click{'s' if clicks != 1 else ''} from 0"
        note(p, [(f"{order[k]} mirror: {angle}°", font), (clicks_text, small)], sides[k])
    badge(px(GEMSTONE), bold, "G", (40, 110, 200, 255))
    note(px(GEMSTONE), [("Gemstone: click it", font), ("when all four are set", small)], "below")
    badge(px(RECEIVER), bold, "C", (40, 150, 70, 255))
    note(px(RECEIVER), [("The light must reach", font), ("this crystal", small)], "right")

    # north arrow and title
    nx, ny = width - 60, 70
    draw.polygon([(nx, ny - 40), (nx - 16, ny), (nx + 16, ny)], fill=(25, 20, 14, 230))
    draw.text((nx, ny + 18), "N", font=bold, fill=(25, 20, 14, 255), anchor="mm")
    draw.rounded_rectangle([10, 10, 640, 92], radius=8, fill=(25, 20, 14, 215))
    draw.text((22, 18), "The desert mirrors", font=title, fill=(255, 240, 210, 255))
    draw.text((22, 58), "Each click: 10° clockwise; the status line shows the angle.", font=small,
              fill=(255, 240, 210, 255))

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "darkpassageway_mirrors.webp"
    image.save(target, "WEBP", quality=86, method=6)
    return target


if __name__ == "__main__":
    print(darkpassageway_mirrors())
