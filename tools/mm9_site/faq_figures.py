#!/usr/bin/env python3
"""Pictures for the guide's FAQ (faq.yml `figures`), written to tools/mm9_site/faq/img/.

    python3 tools/mm9_site/faq_figures.py --capture   # one isolated game boot (about 30 s), then the figures
    python3 tools/mm9_site/faq_figures.py             # the figures from the last capture

sturmfordcity_pedestal.webp: Sturmford City as the party enters it (the map's first start point, facing north, 11:00),
the dimensional travel pedestal ringed and labelled. sturmfordcity_pedestal_near.webp: the pedestal up close. The
pedestal's place is level_generation/projects/mm9r_sturmfordcity/convert.py PEDESTAL; the ring's pixel box below was
read off the 1600x900 capture of the tour here and scales with the capture's size. The HUD is cropped away.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "output/mm9_site_shots/faq"
OUT = Path(__file__).resolve().parent / "faq/img"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ARRIVAL = (2089, -1065, 19723)          # sturmfordcity.scene.yml party_start_points[0], facing north
PEDESTAL = (1529, 54)                   # convert.py PEDESTAL (x, y)
NEAR = (1800, -250, 19710)              # close-up camera, looking at the pedestal
REFERENCE = (1600, 900)                 # the capture size the pixel boxes below are for
CROP = (0, 160, 1330, 690)              # the view without the top bar, buffs, minimap and party frame
NEAR_CROP = (160, 255, 1440, 700)
RING = (350, 375, 470, 565)             # the pedestal and its orb in the arrival capture


def capture() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    for old in SHOTS.glob("*.png"):
        old.unlink()
    near_yaw = math.atan2(PEDESTAL[1] - NEAR[1], PEDESTAL[0] - NEAR[0])
    tour = SHOTS / "tour.yml"
    tour.write_text(
        f"output_dir: {SHOTS}\nsettle_seconds: 2.5\nexit: true\nshots:\n"
        f"  - name: arrival\n    position: [{ARRIVAL[0]}, {ARRIVAL[1]}, {ARRIVAL[2]}]\n    yaw: {math.pi / 2:.4f}\n"
        f"    pitch: -0.04\n    time: \"11:00\"\n    settle_seconds: 4\n"
        f"  - name: near\n    position: [{NEAR[0]}, {NEAR[1]}, {NEAR[2]}]\n    yaw: {near_yaw:.4f}\n"
        f"    pitch: -0.04\n    time: \"11:00\"\n")
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    subprocess.run([str(ROOT / "tools/run_game.sh"), "--isolated", "mm9guide_faq", "--world", "mm9", "--map",
                    "sturmfordcity.blv", "--warmup", "3", "--seconds", "90", "--set",
                    f"debug.screenshot_tour_path={tour}"], cwd=ROOT, env=env, check=True, timeout=300)


def scaled(box: tuple, size: tuple) -> tuple:
    kx, ky = size[0] / REFERENCE[0], size[1] / REFERENCE[1]
    return tuple(round(v * (kx if i % 2 == 0 else ky)) for i, v in enumerate(box))


def pedestal_figure() -> Path:
    source = Image.open(SHOTS / "01-arrival.png").convert("RGB")
    crop = scaled(CROP, source.size)
    image = source.crop(crop).resize((CROP[2] - CROP[0], CROP[3] - CROP[1]), Image.LANCZOS)
    draw = ImageDraw.Draw(image, "RGBA")
    x0, y0, x1, y1 = RING
    x0, x1, y0, y1 = x0 - CROP[0], x1 - CROP[0], y0 - CROP[1], y1 - CROP[1]
    for width, colour in ((9, (20, 15, 10, 200)), (5, (255, 214, 40, 255))):
        draw.ellipse([x0, y0, x1, y1], outline=colour, width=width)

    title = ImageFont.truetype(FONT_BOLD, 40)
    small = ImageFont.truetype(FONT, 30)
    lines = [("Dimensional travel pedestal", title), ("Click it: portals to Jadame, Enroth,", small),
             ("Antagarich and back to Chedian", small)]
    boxes = [draw.textbbox((0, 0), text, font=font) for text, font in lines]
    w = max(b[2] - b[0] for b in boxes) + 28
    h = sum(b[3] - b[1] + 10 for b in boxes) + 16
    bx, by = x1 + 70, y0 - 20
    # the arrow from the label to the ring
    ax, ay = bx, by + h / 2
    tx, ty = x1 + 4, (y0 + y1) / 2 - 20
    draw.line([(ax, ay), (tx, ty)], fill=(20, 15, 10, 200), width=9)
    draw.line([(ax, ay), (tx, ty)], fill=(255, 214, 40, 255), width=5)
    angle = math.atan2(ty - ay, tx - ax)
    head = [(tx, ty), (tx - 22 * math.cos(angle - 0.45), ty - 22 * math.sin(angle - 0.45)),
            (tx - 22 * math.cos(angle + 0.45), ty - 22 * math.sin(angle + 0.45))]
    draw.polygon(head, fill=(255, 214, 40, 255), outline=(20, 15, 10, 200))
    draw.rounded_rectangle([bx, by, bx + w, by + h], radius=10, fill=(25, 20, 14, 225))
    cursor = by + 10
    for (text, font), b in zip(lines, boxes):
        draw.text((bx + 14, cursor), text, font=font, fill=(255, 240, 210, 255) if font is small else
                  (255, 214, 40, 255))
        cursor += b[3] - b[1] + 10

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "sturmfordcity_pedestal.webp"
    image.save(target, "WEBP", quality=86, method=6)
    return target


def near_figure() -> Path:
    source = Image.open(SHOTS / "02-near.png").convert("RGB")
    crop = scaled(NEAR_CROP, source.size)
    image = source.crop(crop).resize((NEAR_CROP[2] - NEAR_CROP[0], NEAR_CROP[3] - NEAR_CROP[1]), Image.LANCZOS)
    target = OUT / "sturmfordcity_pedestal_near.webp"
    image.save(target, "WEBP", quality=84, method=6)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--capture", action="store_true", help="capture the screenshots first (one game boot)")
    args = parser.parse_args()
    if args.capture:
        capture()
    print(pedestal_figure())
    print(near_figure())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
