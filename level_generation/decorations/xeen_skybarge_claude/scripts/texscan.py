"""Scan the shipped MM6-MM8 face textures (assets_source/worlds/mm*/textures_x2) by mean colour and write contact
sheets of the candidates for gold/gilt, wood and cloth (work/scan_<kind>.png). Usage: python3 texscan.py"""
import colorsys
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'work'
rows = []
for w in ('mm6', 'mm7', 'mm8'):
    for p in sorted((ROOT / f'assets_source/worlds/{w}/textures_x2').glob('*.png')):
        im = Image.open(p).convert('RGB').resize((16, 16))
        px = list(im.getdata())
        r, g, b = (sum(c[i] for c in px) / len(px) / 255 for i in range(3))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        rows.append((p, h * 360, s, v))
want = {
    'gold': lambda h, s, v: 35 <= h <= 55 and s > 0.45 and v > 0.55,
    'wood': lambda h, s, v: 18 <= h <= 38 and 0.35 < s < 0.75 and 0.25 < v < 0.6,
    'cloth': lambda h, s, v: (h < 15 or h > 345) and s > 0.5 and v > 0.35,
    'white': lambda h, s, v: s < 0.12 and v > 0.75,
    'green': lambda h, s, v: 140 < h < 190 and s > 0.25 and v > 0.3,
}
for kind, f in want.items():
    pick = [r for r in rows if f(*r[1:])][:120]
    n = 12
    sheet = Image.new('RGB', (n * 132, ((len(pick) + n - 1) // n) * 146 or 146), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, (p, *_rest) in enumerate(pick):
        x, y = (i % n) * 132, (i // n) * 146
        sheet.paste(Image.open(p).convert('RGB').resize((128, 128)), (x + 2, y + 2))
        d.text((x + 2, y + 131), f'{p.parent.parent.name[2]}:{p.stem}', fill=(255, 255, 255))
    sheet.save(OUT / f'scan_{kind}.png')
    print(kind, len(pick))
