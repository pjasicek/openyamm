#!/usr/bin/env python3
"""Draw the MM9 skill trainer marker: an open book in the style of the quest markers.

The quest markers (quest_marker_exclamation.png, quest_marker_question.png) are neutral grey bevelled glyphs with a dark
outline on a 256x256 transparent canvas; the renderer tints them per marker state. This draws the trainer glyph the
same way: page and cover shapes at four times the size, a height field from the distance to each shape's edge, lit from
the upper left, engraved text lines, a dark outline, then one downsample.

Usage: generate_mm9_trainer_marker.py [output.png]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SIZE = 256
SCALE = 4
CANVAS = SIZE * SCALE
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "assets_dev/worlds/mm9/sprites/trainer_marker_book.png"
# The book is drawn in 256 units and shrunk towards its bottom centre, so it sits where the quest glyphs end.
GLYPH_SCALE = 0.84
GLYPH_BOTTOM = 236.0


def to_canvas(x, y):
    return ((128.0 + (x - 128.0) * GLYPH_SCALE) * SCALE, (GLYPH_BOTTOM - (GLYPH_BOTTOM - y) * GLYPH_SCALE) * SCALE)


def polygon_mask(points):
    image = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(image).polygon([to_canvas(x, y) for x, y in points], fill=255)
    return np.array(image) > 127


def curve(start, control, end, steps=48):
    t = np.linspace(0.0, 1.0, steps)[:, None]
    p0, p1, p2 = (np.array(point, dtype=float) for point in (start, control, end))
    return [tuple(point) for point in (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2]


def page(side):
    """One page in canvas units (256 space); side -1 is the left page, +1 the right."""
    spine_x = 128 + side * 4
    outer_x = 128 + side * 108
    top = curve((spine_x, 92), (128 + side * 50, 62), (outer_x, 74))
    outer = curve((outer_x, 74), (outer_x + side * 2, 140), (outer_x, 200))
    bottom = curve((outer_x, 200), (128 + side * 50, 190), (spine_x, 218))
    return polygon_mask(top + outer[1:] + bottom[1:])


def cover():
    """The cover under both pages: a slightly larger open book, seen only along the bottom and outer edges."""
    left = curve((16, 84), (14, 150), (16, 212))
    bottom_left = curve((16, 212), (72, 202), (128, 234))
    bottom_right = curve((128, 234), (184, 202), (240, 212))
    right = curve((240, 212), (242, 150), (240, 84))
    return polygon_mask(left + bottom_left[1:] + bottom_right[1:] + right[1:] + [(128, 120)])


def bevel_height(mask, width):
    distance = ndimage.distance_transform_edt(mask)
    ramp = np.clip(distance / (width * SCALE), 0.0, 1.0)
    return np.sin(ramp * np.pi * 0.5)


def text_lines(side):
    """Engraved text lines on one page, following the page's curve."""
    image = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(image)
    for index in range(4):
        y = 102 + index * 24
        start = (128 + side * 22, y + 6)
        end = (128 + side * 88, y - 6 + index * 2)
        control = (128 + side * 52, y - 10)
        points = [to_canvas(x, py) for x, py in curve(start, control, end, 24)]
        draw.line(points, fill=255, width=int(5 * GLYPH_SCALE * SCALE), joint="curve")
    return np.array(image).astype(float) / 255.0


def shade(height):
    gradient_y, gradient_x = np.gradient(ndimage.gaussian_filter(height, 1.5 * SCALE) * 22.0 * SCALE)
    normal = np.dstack((-gradient_x, -gradient_y, np.full(height.shape, float(SCALE))))
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    light = np.array([-0.55, -0.6, 0.58])
    light /= np.linalg.norm(light)
    diffuse = np.clip((normal * light).sum(axis=2), 0.0, 1.0)
    half = light + np.array([0.0, 0.0, 1.0])
    half /= np.linalg.norm(half)
    specular = np.clip((normal * half).sum(axis=2), 0.0, 1.0) ** 24
    return np.clip(0.36 + 0.5 * diffuse + 0.32 * specular, 0.0, 1.0)


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    left_page, right_page = page(-1), page(1)
    cover_mask = cover() & (ndimage.distance_transform_edt(~(left_page | right_page)) > 3 * SCALE)
    glyph = left_page | right_page | cover_mask

    height = np.maximum(bevel_height(left_page, 12), bevel_height(right_page, 12))
    height = np.maximum(height, 0.65 * bevel_height(cover_mask, 4))
    grooves = text_lines(-1) * left_page + text_lines(1) * right_page
    height -= 0.35 * ndimage.gaussian_filter(grooves, SCALE)
    brightness = shade(height)
    brightness *= 1.0 - 0.45 * grooves
    brightness[cover_mask] *= 0.72

    outline = ndimage.distance_transform_edt(~glyph) <= 7 * SCALE
    outline &= ~glyph
    rgb = np.zeros((CANVAS, CANVAS, 3))
    rgb[glyph] = brightness[glyph, None] * 255.0
    rgb[outline] = (38.0, 40.0, 43.0)
    alpha = (glyph | outline).astype(float) * 255.0

    image = Image.fromarray(np.dstack((rgb, alpha)).astype(np.uint8), "RGBA")
    premultiplied = np.array(image).astype(float)
    premultiplied[..., :3] *= premultiplied[..., 3:4] / 255.0
    small = np.array(Image.fromarray(premultiplied.astype(np.uint8), "RGBA").resize((SIZE, SIZE), Image.LANCZOS))
    small = small.astype(float)
    coverage = np.maximum(small[..., 3:4], 1.0) / 255.0
    small[..., :3] = np.clip(small[..., :3] / coverage, 0.0, 255.0)
    small[small[..., 3] < 1.0, :3] = 0.0
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(small.astype(np.uint8), "RGBA").save(output)
    print(output)


if __name__ == "__main__":
    main()
