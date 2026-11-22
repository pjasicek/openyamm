#!/usr/bin/env python3
"""Emblem masks (white = carved) for the daises and the pedestals: each element's alchemical triangle (fire up,
air up with a bar, water down, earth down with a bar) inside rings; image top = model +Y (away from the front).
Writes work/emblems/<kind>_<element>.png. Usage: emblems.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'work' / 'emblems'
OUT.mkdir(parents=True, exist_ok=True)


def triangle(d, c, r, up, bar, w):
    import math
    pts = []
    for k in range(3):
        a = math.radians(90 + 120 * k) if up else math.radians(-90 + 120 * k)
        pts.append((c + r * math.cos(a), c - r * math.sin(a)))
    d.line(pts + [pts[0]], fill=255, width=w, joint='curve')
    if bar:
        y = c + (-0.12 * r if up else 0.12 * r)
        half = 0.62 * r
        d.line([(c - half, y), (c + half, y)], fill=255, width=w)


def ring(d, c, r, w):
    d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=w)


def flames(d, c, r, n, w):
    """Small tick marks round a ring (the dais's outer band)."""
    import math
    for k in range(n):
        a = 2 * math.pi * k / n
        d.line([(c + r * math.cos(a), c + r * math.sin(a)), (c + (r + 0.05 * c) * math.cos(a),
                                                               c + (r + 0.05 * c) * math.sin(a))], fill=255, width=w)


SYMBOL = {'fire': (True, False), 'air': (True, True), 'water': (False, False), 'earth': (False, True)}
S = 1024
c = S / 2
for el, (up, bar) in SYMBOL.items():
    # the dais: the image spans the disc's diameter
    im = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(im)
    ring(d, c, 0.90 * c, 10)
    ring(d, c, 0.84 * c, 6)
    flames(d, c, 0.70 * c, 24, 8)
    ring(d, c, 0.62 * c, 10)
    triangle(d, c, 0.44 * c, up, bar, 22)
    im.filter(ImageFilter.GaussianBlur(1.6)).save(OUT / f'dais_{el}.png')
    # the pedestal: the image spans the top's diameter
    im = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(im)
    ring(d, c, 0.86 * c, 22)
    triangle(d, c, 0.56 * c, up, bar, 44)
    im.filter(ImageFilter.GaussianBlur(3)).save(OUT / f'pedestal_{el}.png')
print('EMBLEMS', OUT)
