#!/usr/bin/env python3
"""Annotated figures for the Xeen walkthroughs (story/*.yml `figures`), written to tools/xeen_site/story/img/.

    python3 tools/xeen_site/story_figures.py    # needs output/xeen_site (run build_site.py once): plans and points

Each figure is a crop of the guide's own map image (the journal map of a surface map, a floor plan of a dungeon) round
the points of one puzzle, with numbered badges and short notes, as the MM9 guide's story_figures.py draws them. The
points come from the built guide (`data/guide.js`: their place on the floor image), so a figure follows the map when
the guide is rebuilt. The figures sit inside the walkthroughs, which are closed by default: they may give the answers.

asp_pedestals.webp     Q-C5: the eight pedestals round Asp's well, the colour each must show (corners red).
bark_dials.webp        Q-D10: the Temple of Bark's three dials and their settings, the lever and the Crystal Water.
pyramid_niches.webp    M28: the Great Pyramid's eight number niches and the number each takes.
sandro_shrines.webp    Q-F2: the four Shrines of Evil (which to break, which to leave).
sandro_gongs.webp      Q-F2: the gong hall's four gongs and the lever.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "output/xeen_site"
WORLD = ROOT / "assets_dev/worlds/xeen"
OUT = Path(__file__).resolve().parent / "story/img"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIDTH = 1100  # every figure is drawn this wide

RED, BLUE, GOLD, GREEN, GREY = (176, 40, 30, 255), (40, 90, 190, 255), (190, 140, 20, 255), (40, 140, 70, 255), \
    (90, 90, 90, 255)


def guide_maps() -> dict[str, dict]:
    text = (SITE / "data/guide.js").read_text(encoding="utf-8")
    data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    return {m["id"]: m for m in data["maps"]}


class Figure:
    """A crop of one floor image round a set of points, scaled to WIDTH, with badges and notes drawn on it."""

    def __init__(self, map_data: dict, poi_ids: list[str], margin: float = 0.35, min_span: float = 0.0):
        pois = {p["id"]: p for p in map_data["pois"]}
        missing = [i for i in poi_ids if i not in pois]
        if missing:
            raise SystemExit(f"{map_data['id']}: no points {missing} (rebuild the guide?)")
        self.pois = pois
        floor_index = pois[poi_ids[0]]["f"]
        floor = map_data["floors"][floor_index]
        source = Image.open(SITE / floor["img"]).convert("RGB")
        sw, sh = source.size
        us = [pois[i]["u"] * sw for i in poi_ids]
        vs = [pois[i]["v"] * sh for i in poi_ids]
        span = max(max(us) - min(us), max(vs) - min(vs), min_span * sw)
        pad = span * margin + 12
        left, right = max(min(us) - pad, 0), min(max(us) + pad, sw)
        top, bottom = max(min(vs) - pad, 0), min(max(vs) + pad, sh)
        if bottom - top > 1.2 * (right - left):  # a tall strip (the niches' corridor): widen it, at most 6:5
            grow = ((bottom - top) / 1.2 - (right - left)) / 2
            left, right = max(left - grow, 0), min(right + grow, sw)
        self.box = (left, top, right, bottom)
        self.scale = WIDTH / (right - left)
        height = int((bottom - top) * self.scale)
        self.image = source.crop((int(left), int(top), int(right), int(bottom))).resize((WIDTH, height),
                                                                                         Image.LANCZOS)
        self.source_size = (sw, sh)
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        self.font = ImageFont.truetype(FONT, 22)
        self.small = ImageFont.truetype(FONT, 18)
        self.bold = ImageFont.truetype(FONT_BOLD, 24)
        self.title_font = ImageFont.truetype(FONT_BOLD, 28)
        self.taken: list[tuple[float, float, float, float]] = []
        self.badges: list[tuple] = []  # drawn last, over the notes

    def at(self, poi_id: str) -> tuple[float, float]:
        poi = self.pois[poi_id]
        sw, sh = self.source_size
        return (poi["u"] * sw - self.box[0]) * self.scale, (poi["v"] * sh - self.box[1]) * self.scale

    def badge(self, poi_id: str, label: str, fill, radius: int = 22) -> None:
        cx, cy = self.at(poi_id)
        self.badges.append((cx, cy, label, fill, radius))
        self.taken.append((cx - radius - 4, cy - radius - 4, cx + radius + 4, cy + radius + 4))

    def note(self, poi_id: str, lines: list[str], side: str = "auto") -> None:
        """A label box beside a badge, kept inside the figure and clear of the other notes."""
        x, y = self.at(poi_id)
        fonts = [self.font] + [self.small] * (len(lines) - 1)
        boxes = [self.draw.textbbox((0, 0), line, font=f) for line, f in zip(lines, fonts)]
        w = max(b[2] - b[0] for b in boxes) + 20
        h = sum(b[3] - b[1] + 8 for b in boxes) + 12
        width, height = self.image.size
        sides = [side] if side != "auto" else ["right", "left", "below", "above"]
        for choice in sides:
            bx = {"right": x + 32, "left": x - 32 - w}.get(choice, x - w / 2)
            by = {"above": y - 32 - h, "below": y + 32}.get(choice, y - h / 2)
            bx, by = min(max(bx, 8), width - w - 8), min(max(by, 8), height - h - 8)
            rect = (bx, by, bx + w, by + h)
            if not any(rect[0] < o[2] and o[0] < rect[2] and rect[1] < o[3] and o[1] < rect[3] for o in self.taken):
                break
        self.taken.append(rect)
        self.draw.rounded_rectangle(rect, radius=8, fill=(25, 20, 14, 215))
        cursor = rect[1] + 8
        for (line, f), b in zip(zip(lines, fonts), boxes):
            self.draw.text((rect[0] + 10, cursor), line, font=f, fill=(255, 240, 210, 255))
            cursor += b[3] - b[1] + 8

    def title(self, title: str, subtitle: str) -> None:
        w = max(self.draw.textbbox((0, 0), title, font=self.title_font)[2],
                self.draw.textbbox((0, 0), subtitle, font=self.small)[2]) + 28
        rect = (10, 10, 10 + w, 94)
        self.draw.rounded_rectangle(rect, radius=8, fill=(25, 20, 14, 225))
        self.draw.text((22, 18), title, font=self.title_font, fill=(255, 240, 210, 255))
        self.draw.text((22, 60), subtitle, font=self.small, fill=(255, 240, 210, 255))
        self.taken.append(rect)
        nx, ny = self.image.size[0] - 44, 60  # north is up on every plan
        self.draw.polygon([(nx, ny - 36), (nx - 14, ny), (nx + 14, ny)], fill=(25, 20, 14, 230))
        self.draw.text((nx, ny + 16), "N", font=self.bold, fill=(25, 20, 14, 255), anchor="mm")
        self.taken.append((nx - 30, ny - 40, nx + 30, ny + 34))

    def save(self, name: str) -> Path:
        for cx, cy, label, fill, radius in self.badges:
            self.draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill,
                              outline=(20, 15, 10, 255), width=3)
            self.draw.text((cx, cy), label, font=self.bold, fill=(255, 255, 255, 255), anchor="mm")
        OUT.mkdir(parents=True, exist_ok=True)
        target = OUT / name
        self.image.save(target, "WEBP", quality=86, method=6)
        return target


def compass(dx: float, dy: float) -> str:
    """The compass point of an image offset (y down)."""
    angle = (math.degrees(math.atan2(-dy, dx)) + 360) % 360
    return ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"][
        int((angle + 22.5) // 45) % 8]


def asp_pedestals(maps: dict) -> Path:
    pedestals = [f"e{n}" for n in range(90, 98)]
    figure = Figure(maps["xeen_x4"], pedestals + ["e98"], margin=0.45)
    points = [figure.at(p) for p in pedestals]
    cx, cy = sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
    figure.badge("e98", "S", GOLD)
    for poi_id, (x, y) in zip(pedestals, points):
        figure.badge(poi_id, "R" if "-" in compass(x - cx, y - cy) else "B", RED if "-" in compass(x - cx, y - cy)
                     else BLUE)
    for poi_id, (x, y) in zip(pedestals, points):
        side = compass(x - cx, y - cy)
        corner = "-" in side
        figure.note(poi_id, [f"{side.capitalize()}: {'red' if corner else 'blue'}"],
                    "left" if x < cx - 5 else "right" if x > cx + 5 else "above" if y < cy else "below")
    figure.note("e98", ["Rule stone"])
    figure.title("Asp's pedestals", "All start blue; a touch turns one red, another touch blue again.")
    return figure.save("asp_pedestals.webp")


def bark_dials(maps: dict) -> Path:
    figure = Figure(maps["xeen_dd09"], ["e21", "e22", "e23", "e2", "e18"], margin=0.6)
    dials = (("e23", "1", "West dial"), ("e22", "2", "North dial"), ("e21", "3", "East dial"))
    for poi_id, label, _ in dials:
        figure.badge(poi_id, label, RED)
    figure.badge("e2", "L", GOLD)
    figure.badge("e18", "W", GREEN)
    for poi_id, label, where in dials:
        figure.note(poi_id, [f"{where}: set to {label}"])
    figure.note("e2", ["Then pull the lever"])
    figure.note("e18", ["Drink the Crystal Water"])
    figure.title("The Bark dials", "Each dial starts at 1; every 'Turn? Yes' adds one.")
    return figure.save("bark_dials.webp")


def pyramid_niches(maps: dict) -> Path:
    # Each niche's event calls Xeen.pyramidNiche(<index>); index 1..8 takes 3..10 (Xeen.PyramidNiches).
    lua = (WORLD / "events/maps/xeen_dd15.lua").read_text(encoding="utf-8")
    niches = {f"e{event}": int(index) + 2 for event, index in
              re.findall(r"RegisterEvent\((\d+),[^\n]*\n(?:[^\n]*\n){0,2}?\s*Xeen\.pyramidNiche\((\d+),", lua)}
    if len(niches) != 8:
        raise SystemExit(f"pyramid niches: found {len(niches)} of 8")
    order = sorted(niches, key=niches.get)
    figure = Figure(maps["xeen_dd15"], order, margin=0.3)
    for poi_id in order:
        figure.badge(poi_id, str(niches[poi_id]), RED)
    figure.note(order[0], ["Type each niche's number;", "the eighth opens the Overseer's vault"])
    figure.title("The number niches", "Floor 1's number hall: each niche takes the number on its badge.")
    return figure.save("pyramid_niches.webp")


def sandro_shrines(maps: dict) -> Path:
    shrines = [("e82", "1", "Shrine of Minor Evil", "destroy", RED), ("e80", "2", "Shrine of Lesser Evil", "destroy", RED),
               ("e78", "3", "Shrine of Great Evil", "destroy", RED),
               ("e84", "X", "Shrine of Ultimate Evil", "leave it: it throws you out", GREY)]
    figure = Figure(maps["xeen_fd04"], [s[0] for s in shrines], margin=0.5)
    for poi_id, label, name, what, fill in shrines:
        figure.badge(poi_id, label, fill)
    for poi_id, label, name, what, fill in shrines:
        figure.note(poi_id, [name, what])
    figure.title("The Shrines of Evil", "Break the three numbered shrines; leave the fourth until last.")
    return figure.save("sandro_shrines.webp")


def sandro_gongs(maps: dict) -> Path:
    gongs = ["e58", "e60", "e62", "e64"]
    figure = Figure(maps["xeen_fd04"], gongs + ["e68"], margin=0.5)
    for index, poi_id in enumerate(gongs, 1):
        figure.badge(poi_id, str(index), RED)
    figure.badge("e68", "L", GOLD)
    figure.note(gongs[0], ["Ring all four gongs"])
    figure.note("e68", ["Then pull the lever:", "the shutter to the machine hall rises"])
    figure.title("The gong hall", "Open the hall's chest only after the lever.")
    return figure.save("sandro_gongs.webp")


if __name__ == "__main__":
    guide = guide_maps()
    for draw in (asp_pedestals, bark_dials, pyramid_niches, sandro_shrines, sandro_gongs):
        print(draw(guide))
