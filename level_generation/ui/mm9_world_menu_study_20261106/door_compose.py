#!/usr/bin/env python3
"""Four-portal Dimension Door: base, hover overlays and hit zones (README.md)."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
OLD = ROOT / 'assets_dev/engine/ui/gameplay/dimensional_travel'
BASE = W / 'raw/door_base_v2.png'
# Portal interiors in the raw base (1448x1086): centre and radii, measured on review/door_grid.png.
PORTALS = [('jadame', 182, 385), ('enroth', 545, 385), ('antagarich', 906, 385), ('chedian', 1270, 385)]
RX, RY = 121, 136
# Destination views: (image, centre, radius) of the circle to lift. The old hover pictures are drawn at
# (0,46), (180,0) and (180,46) over tpglobal, whose portal centre is about (315,172) with radius 122.
SOURCES = {
    'jadame': (OLD / 'tpjadam1.bmp', (315, 126), 122),
    'enroth': (OLD / 'tpenroth1.bmp', (135, 172), 122),
    'antagarich': (OLD / 'tpantag1.bmp', (135, 126), 122),
    'chedian': (W / 'raw/chedian_vista_v1.png', (627, 627), 560),
}
OUT_SIZE, NATIVE = (1280, 960), (640, 480)


def view(name):
    path, (cx, cy), radius = SOURCES[name]
    image = Image.open(path).convert('RGB').crop((cx - radius, cy - radius, cx + radius, cy + radius))
    return image.resize((2 * RX, 2 * RY), Image.LANCZOS)


def main():
    base = Image.open(BASE).convert('RGB')
    lit = base.copy()
    mask = Image.new('L', (2 * RX, 2 * RY), 0)
    ImageDraw.Draw(mask).ellipse([6, 6, 2 * RX - 6, 2 * RY - 6], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(7))
    for name, cx, cy in PORTALS:
        lit.paste(view(name), (cx - RX, cy - RY), mask)
    scale = OUT_SIZE[0] / base.width
    final = W / 'final' / 'dimension_door'
    final.mkdir(parents=True, exist_ok=True)
    base_out = base.resize(OUT_SIZE, Image.LANCZOS)
    lit_out = lit.resize(OUT_SIZE, Image.LANCZOS)
    base_out.save(final / 'tpglobal4.png')
    lit_out.save(final / 'all_lit.png')
    zones = []
    width = NATIVE[0] // len(PORTALS)
    for index, (name, cx, cy) in enumerate(PORTALS):
        # Hover picture: the lit portal's box (frame included), at x2 like the other HUD art; drawn at its native box.
        box = [round((cx - RX - 22) * scale), round((cy - RY - 40) * scale), round((cx + RX + 22) * scale),
               round((cy + RY + 30) * scale)]
        lit_out.crop(box).save(final / f'tp{name}4.png')
        zones.append({'destination': name, 'icon': f'tp{name}4', 'icon_x': box[0] // 2, 'icon_y': box[1] // 2,
                      'icon_width': (box[2] - box[0]) // 2, 'icon_height': (box[3] - box[1]) // 2,
                      'hit_x': index * width, 'hit_y': 0, 'hit_width': width, 'hit_height': NATIVE[1]})
    (final / 'zones.json').write_text(json.dumps(zones, indent=2) + '\n')
    # Review: hover over Chedian, zones drawn.
    review = base_out.copy()
    last = zones[-1]
    review.paste(Image.open(final / 'tpchedian4.png'), (last['icon_x'] * 2, last['icon_y'] * 2))
    draw = ImageDraw.Draw(review)
    for zone in zones:
        x = zone['hit_x'] * 2
        draw.rectangle([x, 0, x + zone['hit_width'] * 2 - 1, 959], outline=(255, 210, 80), width=2)
        draw.text((x + 10, 930), f"{zone['destination']}: hit {zone['hit_x']}-{zone['hit_x'] + zone['hit_width']}",
                  fill=(255, 230, 150))
    review.save(W / 'review' / 'door_hover_chedian_zones.png')
    print(json.dumps(zones))


if __name__ == '__main__':
    main()
