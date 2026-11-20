#!/usr/bin/env python3
"""The docked combat log's line glyphs: a sword (a melee hit), a bow (a missile) and a skull (a killing blow).

White shapes with a dark outline on transparency; the panel tints them (the quad tint multiplies, so the outline
stays dark and reads like the text's shadow). Drawn at 8x and downsampled to 32 px, the x2 size of a log line.

  python3 level_generation/ui/maw_combat_log_20261024/make_glyphs.py
writes assets_dev/engine/icons_x2/combat_log_{melee,shoot,kill}.png.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets_dev/engine/icons_x2"
SIZE = 32
SS = 8
BIG = SIZE * SS


def canvas():
    return Image.new("L", (BIG, BIG), 0)


def p(x, y):
    """A point in 32 px units on the big canvas."""
    return (x * SS, y * SS)


def sword():
    mask = canvas()
    d = ImageDraw.Draw(mask)
    # The blade on the diagonal from lower left to upper right, a tapered point.
    d.polygon([p(10.2, 19.6), p(24.2, 5.6), p(27.4, 4.6), p(26.4, 7.8), p(12.4, 21.8)], fill=255)
    # The crossguard across the blade.
    d.line([p(7.6, 17.0), p(15.0, 24.4)], fill=255, width=int(2.6 * SS))
    # The grip and pommel.
    d.line([p(11.2, 20.8), p(6.2, 25.8)], fill=255, width=int(2.2 * SS))
    d.ellipse([p(3.4, 25.6), p(7.0, 29.2)], fill=255)
    return mask


def bow():
    mask = canvas()
    d = ImageDraw.Draw(mask)
    # The bow's limbs, an arc opening to the right, and its string.
    d.arc([p(3.0, 3.0), p(21.0, 29.0)], start=115, end=245, fill=255, width=int(2.6 * SS))
    d.line([p(8.6, 4.8), p(8.6, 27.2)], fill=255, width=int(1.0 * SS))
    # The arrow, nocked on the string and pointing right.
    d.line([p(6.0, 16.0), p(25.0, 16.0)], fill=255, width=int(1.8 * SS))
    d.polygon([p(29.4, 16.0), p(23.4, 11.6), p(24.6, 16.0), p(23.4, 20.4)], fill=255)
    d.polygon([p(5.0, 16.0), p(2.4, 12.6), p(4.6, 12.6), p(7.2, 16.0), p(4.6, 19.4), p(2.4, 19.4)], fill=255)
    return mask


def skull():
    mask = canvas()
    d = ImageDraw.Draw(mask)
    # The cranium and the jaw.
    d.ellipse([p(5.0, 3.0), p(27.0, 23.0)], fill=255)
    d.rounded_rectangle([p(10.0, 17.0), p(22.0, 28.0)], radius=2.5 * SS, fill=255)
    hole = canvas()
    h = ImageDraw.Draw(hole)
    # The eyes, the nose and the gaps between the teeth.
    h.ellipse([p(8.6, 11.0), p(14.8, 17.6)], fill=255)
    h.ellipse([p(17.2, 11.0), p(23.4, 17.6)], fill=255)
    h.polygon([p(16.0, 17.6), p(14.4, 21.0), p(17.6, 21.0)], fill=255)
    for x in (13.6, 16.0, 18.4):
        h.line([p(x, 24.0), p(x, 28.0)], fill=255, width=int(1.1 * SS))
    return ImageChops.subtract(mask, hole)


def finish(mask):
    """White fill inside a dark outline, downsampled to 32 px."""
    outline = mask.filter(ImageFilter.MaxFilter(2 * SS + 1))
    image = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    image.paste((12, 10, 6, 235), (0, 0), outline)
    image.paste((255, 255, 255, 255), (0, 0), mask)
    return image.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    for name, draw in (("melee", sword), ("shoot", bow), ("kill", skull)):
        path = OUT / f"combat_log_{name}.png"
        finish(draw()).save(path)
        path.chmod(0o644)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
