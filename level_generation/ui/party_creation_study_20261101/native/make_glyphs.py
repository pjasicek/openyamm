#!/usr/bin/env python3
"""White symbol glyphs for the native party creation screen (approach C2).

The menu fonts are Windows-1252 bitmap recreations without the mockup's symbols (◆ ✓ ○ • ▲ ▼ ★ ✦ ▶ −), so the screen
draws these 48x48 white shapes tinted with drawTextureColor. Drawn at 8x and downsampled for clean edges.

    python3 level_generation/ui/party_creation_study_20261101/native/make_glyphs.py
"""
import math
import os

from PIL import Image, ImageDraw

SIZE = 48
SUPER = 8
OUT = os.path.join(os.path.dirname(__file__), "../../../../assets_dev/engine/hud_x2/menus")


def canvas():
    image = Image.new("L", (SIZE * SUPER, SIZE * SUPER), 0)
    return image, ImageDraw.Draw(image)


def s(value):
    return value * SUPER


def save(name, image):
    alpha = image.resize((SIZE, SIZE), Image.LANCZOS)
    rgba = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    rgba.putalpha(alpha)
    path = os.path.join(OUT, f"omenu_glyph_{name}.png")
    rgba.save(path)
    os.chmod(path, 0o644)


def polygon(points):
    image, draw = canvas()
    draw.polygon([(s(x), s(y)) for x, y in points], fill=255)
    return image


def star(points, outer, inner):
    result = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / points
        result.append((24 + radius * math.cos(angle), 24 + radius * math.sin(angle)))
    return result


def main():
    save("diamond", polygon([(24, 6), (42, 24), (24, 42), (6, 24)]))

    image, draw = canvas()
    draw.line([(s(9), s(25)), (s(19), s(35)), (s(39), s(12))], fill=255, width=s(6), joint="curve")
    for x, y in ((9, 25), (19, 35), (39, 12)):
        draw.ellipse([s(x - 3), s(y - 3), s(x + 3), s(y + 3)], fill=255)
    save("check", image)

    image, draw = canvas()
    draw.ellipse([s(7), s(7), s(41), s(41)], outline=255, width=s(4))
    save("ring", image)

    image, draw = canvas()
    draw.ellipse([s(15), s(15), s(33), s(33)], fill=255)
    save("dot", image)

    save("up", polygon([(24, 9), (41, 38), (7, 38)]))
    save("down", polygon([(7, 10), (41, 10), (24, 39)]))
    save("star", polygon(star(5, 21, 9)))
    save("spark", polygon(star(4, 21, 6)))
    save("play", polygon([(12, 8), (40, 24), (12, 40)]))

    image, draw = canvas()
    draw.rectangle([s(8), s(21), s(40), s(27)], fill=255)
    save("minus", image)


if __name__ == "__main__":
    main()
