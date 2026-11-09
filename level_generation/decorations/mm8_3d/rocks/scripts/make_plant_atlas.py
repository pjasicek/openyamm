#!/usr/bin/env python3
"""Procedural plant atlas for the rune stones (our own work, no external sources): 1024 x 1024 RGBA, painted at 2x and
downsampled. Colours follow the sprites rock65/68/69 (ivy green, orange autumn leaves, white lilies with yellow
hearts, small green sprigs, grass) plus a bark strip for the woody vines. Writes textures/plants_{basecolor,normal,mr}.png
and textures/plants_regions.json (Blender UV rectangles [u0, v0, u1, v1], v up, for each element).
Usage: make_plant_atlas.py"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures'); os.makedirs(OUT, exist_ok=True)
S = 2048                                         # painted size (2x)
rng = np.random.default_rng(65)
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
height = Image.new('L', (S, S), 0)               # relief for the normal map
draw = ImageDraw.Draw(img); hdraw = ImageDraw.Draw(height)
regions = {}


def region(name, x0, y0, x1, y1):
    """Record a cell (painted pixels, y down) as Blender UVs (v up)."""
    regions.setdefault(name, []).append([x0 / S, 1 - y1 / S, x1 / S, 1 - y0 / S])


def shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c[:3]) + (255,)


def ivy(cx, cy, size, angle, base):
    """Five-lobed ivy leaf, tip up, with pale veins."""
    pts = []
    lobes = [(0, 1.0), (55, 0.62), (100, 0.5), (-100, 0.5), (-55, 0.62)]
    for i in range(160):
        t = i / 160 * 2 * math.pi
        r = 0.42
        for a, l in lobes:
            d = math.atan2(math.sin(t - math.radians(a + 90)), math.cos(t - math.radians(a + 90)))
            r += (l - 0.25) * math.exp(-(d / 0.42) ** 2)
        if math.sin(t) < -0.6:                   # notch at the stalk
            r *= 0.7 + 0.3 * abs(math.cos(t))
        x, y = r * math.cos(t), -r * math.sin(t)
        ca, sa = math.cos(angle), math.sin(angle)
        pts.append((cx + size * 0.5 * (x * ca - y * sa), cy + size * 0.5 * (x * sa + y * ca)))
    draw.polygon(pts, fill=base)
    hdraw.polygon(pts, fill=150)
    # darker edge band and lighter centre
    inner = [(cx + (x - cx) * 0.75, cy + (y - cy) * 0.75) for x, y in pts]
    draw.polygon(inner, fill=shade(base, 1.12))
    hdraw.polygon(inner, fill=190)
    vein = shade(base, 1.25)
    for a, l in lobes:
        t = math.radians(a + 90) + angle
        draw.line([(cx, cy + size * 0.12), (cx + math.cos(t) * size * 0.45 * l, cy - math.sin(t) * size * 0.45 * l)],
                  fill=vein, width=max(2, int(size / 60)))
        hdraw.line([(cx, cy + size * 0.12), (cx + math.cos(t) * size * 0.45 * l, cy - math.sin(t) * size * 0.45 * l)],
                   fill=120, width=max(2, int(size / 60)))


def leaf(cx, cy, length, width, angle, colour, vein=True):
    """Simple pointed oval leaf from (cx, cy) along angle (radians, 0 = up)."""
    pts = []
    for i in range(41):
        t = i / 40
        w = width * math.sin(math.pi * t) ** 0.8 * (1 - 0.3 * t)
        pts.append((t, w))
    poly = [(t, w) for t, w in pts] + [(t, -w) for t, w in reversed(pts)]
    ca, sa = math.cos(angle), math.sin(angle)
    xy = [(cx + sa * t * length + ca * w, cy - ca * t * length + sa * w) for t, w in poly]
    draw.polygon(xy, fill=colour); hdraw.polygon(xy, fill=170)
    if vein:
        draw.line([(cx, cy), (cx + sa * length * 0.9, cy - ca * length * 0.9)], fill=shade(colour, 1.35),
                  width=max(1, int(width / 6)))


def lily(cx, cy, size):
    """White six-petal flower with a yellow heart, seen from above at an angle."""
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.3
        leaf(cx, cy, size * 0.5, size * 0.14, a, (238, 236, 228, 255), vein=False)
        draw.line([(cx, cy), (cx + math.sin(a) * size * 0.38, cy - math.cos(a) * size * 0.38)], fill=(205, 200, 190, 255),
                  width=3)
    draw.ellipse([cx - size * 0.08, cy - size * 0.08, cx + size * 0.08, cy + size * 0.08], fill=(226, 190, 40, 255))
    for k in range(6):
        a = k / 6 * 2 * math.pi
        draw.ellipse([cx + math.sin(a) * size * 0.1 - 5, cy - math.cos(a) * size * 0.1 - 5,
                      cx + math.sin(a) * size * 0.1 + 5, cy - math.cos(a) * size * 0.1 + 5], fill=(200, 140, 30, 255))


# ivy leaves: four 512 cells (painted), rows y 0..1024, x 0..1024
for i in range(4):
    x0, y0 = (i % 2) * 512, (i // 2) * 512
    base = [(52, 112, 38, 255), (60, 124, 42, 255), (44, 98, 34, 255), (70, 130, 46, 255)][i]
    ivy(x0 + 256, y0 + 266, 470, rng.uniform(-0.15, 0.15), base)
    region('ivy', x0, y0, x0 + 512, y0 + 512)
# orange autumn leaf sprays (rock68): two cells
for i in range(2):
    x0, y0 = i * 512, 1024
    for k in range(9):
        a = rng.uniform(-1.2, 1.2); r = rng.uniform(40, 170)
        c = [(214, 108, 26, 255), (190, 78, 20, 255), (226, 136, 40, 255), (168, 62, 18, 255)][k % 4]
        leaf(x0 + 256 + math.sin(a) * r * 0.6, y0 + 300 - math.cos(a) * r * 0.5, rng.uniform(130, 190),
             rng.uniform(34, 50), a * 0.9, c)
    draw.line([(x0 + 256, y0 + 500), (x0 + 256, y0 + 280)], fill=(90, 50, 25, 255), width=8)
    region('orange', x0, y0, x0 + 512, y0 + 512)
# white lilies (rock68): one cell with three flowers and a leaf rosette
x0, y0 = 0, 1536
for k in range(5):
    a = rng.uniform(-1.3, 1.3)
    leaf(x0 + 256, y0 + 470, rng.uniform(250, 330), 40, a, (58, 110, 40, 255))
lily(x0 + 256, y0 + 200, 330)
region('lily', x0, y0, x0 + 512, y0 + 512)
# grass tuft
x0, y0 = 512, 1536
for k in range(26):
    a = rng.uniform(-0.6, 0.6); ln = rng.uniform(250, 470)
    c = (int(rng.uniform(60, 110)), int(rng.uniform(110, 150)), int(rng.uniform(30, 60)), 255)
    bx = x0 + 256 + rng.uniform(-60, 60)
    pts = [(bx - 8, y0 + 510), (bx + math.sin(a) * ln, y0 + 510 - math.cos(a) * ln), (bx + 8, y0 + 510)]
    draw.polygon(pts, fill=c); hdraw.polygon(pts, fill=160)
region('grass', x0, y0, x0 + 512, y0 + 512)
# green sprig (small shrub branch with paired leaves): x 1024..1536, y 0..2048
x0 = 1024
draw.line([(x0 + 256, 2040), (x0 + 250, 60)], fill=(82, 70, 40, 255), width=10)
for k in range(15):
    y = 1900 - k * 120
    for side in (-1, 1):
        leaf(x0 + 252, y, rng.uniform(150, 210) * (1 - k * 0.025), 50, side * rng.uniform(0.9, 1.3),
             [(56, 116, 40, 255), (72, 132, 48, 255), (48, 100, 36, 255)][(k + side) % 3])
leaf(x0 + 250, 120, 160, 46, 0, (70, 130, 46, 255))
region('sprig', x0, 0, x0 + 512, 2048)
# bark strip (vines): x 1536..2048, v along the vine
bark = np.zeros((S, 512, 3), np.float32)
yy = np.arange(S)[:, None]; xx = np.arange(512)[None, :]
streak = np.zeros((S, 512), np.float32)
for k in range(40):
    f = rng.uniform(0.01, 0.06); ph = rng.uniform(0, 6.28); amp = rng.uniform(0.2, 1.0)
    streak += amp * np.sin(xx * f * 6.28 / 8 + np.sin(yy * rng.uniform(0.002, 0.01) + ph) * 3 + ph)
streak = (streak - streak.min()) / (streak.max() - streak.min())
noise = rng.normal(size=(S // 8, 64)); noise = np.kron(noise, np.ones((8, 8)))
v = np.clip(0.55 + (streak - 0.5) * 0.8 + noise * 0.06, 0, 1)
# two strips from the same relief: brown vine bark (left half) and the grey-green root of rock68 (right half)
for x0, col, name in ((1536, (118, 74, 44), 'bark'), (1792, (104, 108, 82), 'root')):
    half = v[:, :256]
    tone = (np.array(col, np.float32) * (0.55 + 0.75 * half[..., None])).clip(0, 255)
    img.paste(Image.fromarray(np.dstack([tone, np.full((S, 256), 255)]).astype(np.uint8), 'RGBA'), (x0, 0))
    height.paste(Image.fromarray((half * 255).astype(np.uint8), 'L'), (x0, 0))
    region(name, x0, 0, x0 + 256, 2048)

# downsample, bleed colour into transparent texels (no dark fringes under mipmaps), normal from relief
small = img.resize((1024, 1024), Image.LANCZOS)
a = np.asarray(small).astype(np.float32)
rgb, alpha = a[..., :3], a[..., 3:4] / 255
filled = rgb * alpha; weight = alpha.copy()
for r in (2, 4, 8, 16, 32, 64):
    blur_rgb = np.asarray(Image.fromarray(filled.clip(0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(r))).astype(np.float32)
    blur_w = np.asarray(Image.fromarray((weight[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(r))).astype(np.float32)[..., None] / 255
    hole = weight < 0.5
    rgb = np.where(hole, blur_rgb / np.maximum(blur_w, 1e-3), rgb)
    filled = np.where(hole, blur_rgb, filled); weight = np.where(hole, blur_w, weight)
out = np.dstack([rgb.clip(0, 255), (alpha * 255)]).astype(np.uint8)
Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'plants_basecolor.png'))
h = np.asarray(height.resize((1024, 1024), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
dx = np.gradient(h, axis=1) * 6; dy = -np.gradient(h, axis=0) * 6        # image rows run down, +y is up the image
n = np.dstack([-dx, -dy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'plants_normal.png'))
mr = np.zeros((512, 512, 3), np.uint8); mr[..., 1] = 150                 # roughness ~0.6, no metal
mr[:, 384:, 1] = 225                                                      # bark rougher
Image.fromarray(mr, 'RGB').save(os.path.join(OUT, 'plants_mr.png'))
json.dump(regions, open(os.path.join(OUT, 'plants_regions.json'), 'w'), indent=1)
print('ATLAS', OUT, {k: len(v) for k, v in regions.items()})
