#!/usr/bin/env python3
"""MM9's Town Portal screen (TPChedian) from the Codex repaint (README.md).

    python3 compose.py raw/townportal_bg_v2.png raw/table_wood_v2.png

Writes final/tpchedian.png (1280x960, the x2 of the 640x480 screen), final/tp<city>.png (the hover pictures: the
background under the city's box, brightened, with a golden glow round the city), final/rows.txt (the six TPChedian
rows' Icon X/Y/Width/Height for engine/data_tables/town_portal_switch.txt, 640x480 units) and review/boxes.png.

The repaint keeps MM9's map at one uniform scale (its inner red border measured against TOWNPORTALBG.pcx's), so
MM9's own city buttons (TOWNPORTAL-COORDS.txt, 800x600) map onto it. The frame is laid on an empty table so that it
ends above the continent buttons and the Close button (engine/ui/gameplay/town_portal.yml, from y 447 of 480); the
destination label is printed over the frame's lower margin, as on the other continents' maps.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W = Path(__file__).resolve().parent
PORTAL = W.parents[2] / "mm9/extracted/ART/ART/INTERFACESCREENS/PORTAL"
CANVAS = (1280, 960)
# The repaint's map against MM9's 800x600 original: v2 = MAP_SCALE * original + MAP_OFFSET (inner red border
# 71..624 x 78..514 against 204..1151 x 132..878).
MAP_SCALE = (947 / 553, 746 / 436)
MAP_OFFSET = (204 - 71 * 947 / 553, 132 - 78 * 746 / 436)
# The repaint's frame (outer edge) and the shadow margin cut with it.
FRAME = (112, 26, 1244, 934)
SHADOW = 14
# Where the frame goes on the canvas: its top left, and its height (ends at y 880 of 960, above the buttons' 894).
FRAME_AT = (26, 8)
FRAME_HEIGHT = 872
# MM9's city buttons, 800x600 (TOWNPORTAL-COORDS.txt), in the TPChedian rows' order.
CITIES = [
    ("thjorgard", (388, 243, 80, 58)),
    ("sturmford", (511, 301, 66, 58)),
    ("drangheim", (503, 363, 70, 58)),
    ("guberland", (546, 431, 66, 58)),
    ("frosgard", (398, 106, 76, 58)),
    ("thronheim", (275, 185, 60, 58)),
]

# The cities' centres in the repaint, measured on review/city_centres.png (the first layout, frame at (30, 14) and 782
# high) and carried back into the repaint's pixels so that they follow FRAME_AT and FRAME_HEIGHT.
CENTRES = {
    name: (112 + (x - 30) * 908 / 782, 26 + (y - 14) * 908 / 782)
    for name, (x, y) in {
        "frosgard": (635, 187), "thronheim": (461, 316), "thjorgard": (611, 391),
        "sturmford": (791, 475), "drangheim": (787, 566), "guberland": (835, 672),
    }.items()
}


def city_outline(name: str, centre: tuple[int, int], scale: float, origin: tuple[int, int],
                 size: tuple[int, int]) -> tuple[Image.Image, Image.Image]:
    """MM9's highlight outline round the city (its <CITY>-HIGHLIGHTA.pcx against -NORMAL.pcx), as a smooth stroke: the
    outline's filled shape scaled to the repaint, centred on the repainted city, smoothed, and the band just outside it.
    Returns the stroke and a soft glow, both masks of `size` at `origin` on the canvas."""
    from scipy import ndimage
    normal = np.asarray(Image.open(PORTAL / f"{name.upper()}-NORMAL.pcx").convert("RGB")).astype(int)
    lit = np.asarray(Image.open(PORTAL / f"{name.upper()}-HIGHLIGHTA.pcx").convert("RGB")).astype(int)
    outline = np.abs(normal - lit).sum(2) > 60
    shape = ndimage.binary_fill_holes(outline)
    ys, xs = np.nonzero(shape)
    factor = MAP_SCALE[0] * scale
    # the outline's own width (about 2 MM9 pixels) is part of the filled shape: the stroke goes on its inner half
    small = Image.fromarray((ndimage.binary_erosion(shape, iterations=1) * 255).astype("uint8"))
    big = small.resize((round(small.width * factor), round(small.height * factor)), Image.BICUBIC)
    big = big.filter(ImageFilter.GaussianBlur(factor * 0.9)).point(lambda v: 255 if v >= 128 else 0)
    canvas = Image.new("L", CANVAS, 0)
    canvas.paste(big, (round(centre[0] - xs.mean() * factor), round(centre[1] - ys.mean() * factor)))
    # a little room round the repainted miniature, which is not MM9's to the pixel
    inside = ndimage.binary_dilation(np.asarray(canvas) > 0, iterations=4)
    ring = ndimage.binary_dilation(inside, iterations=4) & ~inside
    stroke = Image.fromarray((ring * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.8))
    glow = Image.fromarray((ndimage.binary_dilation(inside, iterations=9) & ~inside).astype("uint8") * 255)
    glow = glow.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.55))
    box = (origin[0], origin[1], origin[0] + size[0], origin[1] + size[1])
    return stroke.crop(box), glow.crop(box)


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - size[0]) // 2, (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def main() -> int:
    repaint = Image.open(W / sys.argv[1]).convert("RGB")
    wood = cover(Image.open(W / sys.argv[2]).convert("RGB"), CANVAS)
    scale = FRAME_HEIGHT / (FRAME[3] - FRAME[1])

    # The frame with its shadow margin, feathered over the margin so the repaint's own table fades into the new one.
    box = (FRAME[0] - SHADOW, FRAME[1] - SHADOW, FRAME[2] + SHADOW, FRAME[3] + SHADOW)
    frame = repaint.crop(box)
    size = (round(frame.width * scale), round(frame.height * scale))
    frame = frame.resize(size, Image.LANCZOS)
    margin = round(SHADOW * scale)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle((margin, margin, size[0] - margin - 1, size[1] - margin - 1), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(margin * 0.45))
    inner = Image.new("L", size, 0)
    ImageDraw.Draw(inner).rectangle((margin, margin, size[0] - margin - 1, size[1] - margin - 1), fill=255)
    mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(inner)))
    # a soft shadow of the frame on the new table
    shadow = Image.new("L", CANVAS, 0)
    at = (FRAME_AT[0] - margin, FRAME_AT[1] - margin)
    ImageDraw.Draw(shadow).rectangle((at[0] + margin + 6, at[1] + margin + 8, at[0] + size[0] - margin + 6,
                                      at[1] + size[1] - margin + 8), fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.composite(Image.new("RGB", CANVAS, (12, 7, 3)), wood, shadow)
    canvas.paste(frame, at, mask)
    canvas.save(W / "final/tpchedian.png")

    def to_canvas_from_repaint(vx: float, vy: float) -> tuple[float, float]:
        return FRAME_AT[0] + (vx - FRAME[0]) * scale, FRAME_AT[1] + (vy - FRAME[1]) * scale

    def to_canvas(x: float, y: float) -> tuple[float, float]:
        return to_canvas_from_repaint(MAP_SCALE[0] * x + MAP_OFFSET[0], MAP_SCALE[1] * y + MAP_OFFSET[1])

    review = canvas.copy()
    draw = ImageDraw.Draw(review)
    rows = []
    for name, (x, y, w, h) in CITIES:
        x0, y0 = to_canvas(x, y)
        x1, y1 = to_canvas(x + w, y + h)
        # MM9's button size, centred on the repainted city (the repaint moved some miniatures a little)
        # (to a thousandth: a centre measured on the first layout lands on it exactly, not a hair either side of a
        # half-unit box edge)
        cx, cy = (round(value, 3) for value in to_canvas_from_repaint(*CENTRES[name]))
        # plus room for the stroke and its glow (6 units)
        iw, ih = int(round((x1 - x0) / 2)) + 6, int(round((y1 - y0) / 2)) + 6
        ix, iy = int(round(cx / 2 - iw / 2)), int(round(cy / 2 - ih / 2))
        crop = canvas.crop((ix * 2, iy * 2, (ix + iw) * 2, (iy + ih) * 2))
        stroke, glow = city_outline(name, (cx, cy), scale, (ix * 2, iy * 2), crop.size)
        hover = ImageEnhance.Brightness(crop).enhance(1.08)
        hover = Image.composite(Image.new("RGB", crop.size, (255, 196, 90)), hover, glow)
        hover = Image.composite(Image.new("RGB", crop.size, (255, 142, 24)), hover, stroke)
        hover.save(W / f"final/tp{name}.png")
        rows.append(f"{name}\t{ix}\t{iy}\t{iw}\t{ih}")
        draw.rectangle((ix * 2, iy * 2, (ix + iw) * 2, (iy + ih) * 2), outline=(255, 0, 255), width=2)
        review.paste(hover, (ix * 2, iy * 2))
    # the destination label and the Close button (town_portal.yml)
    draw.rectangle((680, 804, 1160, 860), outline=(0, 255, 255), width=2)
    draw.rectangle((1108, 894, 1274, 954), outline=(0, 255, 255), width=2)
    review.save(W / "review/boxes.png")
    (W / "final/rows.txt").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
