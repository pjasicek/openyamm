#!/usr/bin/env python3
"""Five-portal Dimension Door (README.md): the backdrop tpglobal5, the five lit doors and their rects.

Adapted from ../mm9_world_menu_study_20261106/door_compose.py (the four-portal screen). Writes final/ and
review/; `--install` copies the backdrop and the lit doors into the Xeen world's ui/gameplay/dimensional_travel/.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
STUDY4 = W.parent / 'mm9_world_menu_study_20261106'
BASE = W / 'raw/door_base5_v1.png'
INSTALL = ROOT / 'assets_dev/worlds/xeen/ui/gameplay/dimensional_travel'
# Portal interiors in the raw base (1448x1086): centre and radii, measured by the mist's blue tint.
PORTALS = [('jadame', 161, 384), ('enroth', 452, 383), ('antagarich', 723, 382), ('chedian', 996, 383),
           ('xeen', 1289, 382)]
RX, RY = 101, 124
# Destination views: (image, centre, radius) of the circle to lift; the first three are the original hover pictures,
# Chedian's the four-portal study's vista, Xeen's new (raw/xeen_vista_v1.png).
SOURCES = {
    'jadame': (W / 'refs/tpjadam1.png', (315, 126), 122),
    'enroth': (W / 'refs/tpenroth1.png', (135, 172), 122),
    'antagarich': (W / 'refs/tpantag1.png', (135, 126), 122),
    'chedian': (STUDY4 / 'raw/chedian_vista_v1.png', (627, 627), 560),
    'xeen': (W / 'raw/xeen_vista_v1.png', (627, 627), 575),
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
    ImageDraw.Draw(mask).ellipse([5, 5, 2 * RX - 5, 2 * RY - 5], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    for name, cx, cy in PORTALS:
        lit.paste(view(name), (cx - RX, cy - RY), mask)
    scale = OUT_SIZE[0] / base.width
    final = W / 'final'
    final.mkdir(parents=True, exist_ok=True)
    base_out = base.resize(OUT_SIZE, Image.LANCZOS)
    lit_out = lit.resize(OUT_SIZE, Image.LANCZOS)
    base_out.save(final / 'tpglobal5.png')
    lit_out.save(final / 'all_lit5.png')
    places = []
    width = NATIVE[0] // len(PORTALS)
    for index, (name, cx, cy) in enumerate(PORTALS):
        # The lit door: the portal's box with its ring, at x2 like the other HUD art, drawn at its native rect.
        left, top = round((cx - RX - 20) * scale), round((cy - RY - 34) * scale)
        right, bottom = round((cx + RX + 20) * scale), round((cy + RY + 26) * scale)
        left, top = left - left % 2, top - top % 2
        right, bottom = right - right % 2, bottom - bottom % 2
        lit_out.crop((left, top, right, bottom)).save(final / f'tp{name}5.png')
        places.append({'door': name, 'picture': [left // 2, top // 2, (right - left) // 2, (bottom - top) // 2],
                       'hover': [index * width, 0, width, NATIVE[1]]})
    (final / 'places.json').write_text(json.dumps(places, indent=2) + '\n')
    review = base_out.copy()
    for place in places[3:]:
        x, y = place['picture'][0] * 2, place['picture'][1] * 2
        review.paste(Image.open(final / f"tp{place['door']}5.png"), (x, y))
    draw = ImageDraw.Draw(review)
    for place in places:
        x, y, w, h = (2 * v for v in place['picture'])
        draw.rectangle([x, y, x + w - 1, y + h - 1], outline=(120, 220, 255), width=2)
        hx = place['hover'][0] * 2
        draw.rectangle([hx, 0, hx + place['hover'][2] * 2 - 1, 959], outline=(255, 210, 80), width=2)
        draw.text((hx + 10, 930), f"{place['door']}: picture {place['picture']}", fill=(255, 230, 150))
    (W / 'review').mkdir(exist_ok=True)
    review.save(W / 'review' / 'door5_hover_zones.png')
    print(json.dumps(places))
    if '--install' in sys.argv:
        INSTALL.mkdir(parents=True, exist_ok=True)
        for name in ['tpglobal5'] + [f'tp{p[0]}5' for p in PORTALS]:
            target = INSTALL / f'{name}.png'
            shutil.copyfile(final / f'{name}.png', target)
            target.chmod(0o644)
        print('installed into', INSTALL)


if __name__ == '__main__':
    main()
