#!/usr/bin/env python3
"""Procedural 512² card atlas for one New Sorpigal flower (work/<id>/atlas_basecolor.png RGBA, atlas_normal.png):
2 x 2 cells of 256 px, painted with numpy at 4x supersampling from leaf/petal shapes (no external images):
  gazania (6flower02): cells 0/1 bushy dome clumps of grey-green leaves pointing out from the clump; cell 2 an open
    orange daisy head (17 rays, brown-black ring with pale spots, yellow-brown disc) seen face on, mapped onto small
    cup meshes; cell 3 a green stem strip (u 0.02-0.08 of the cell).
  crocus (6flower07): cells 0/1 grass-like leaves with a pale mid stripe; cell 2 a tileable strip of six goblet petals
    (u around, v up; pale base, purple body, rounded tips) wrapped round lathed bloom meshes; cell 3 the bloom's
    stamen centre (disc round the cell centre) and a pale stem strip (u 0.02-0.08).
Colours match the native sprite means (foliage ~44/64/26 and ~52/72/35, gazania orange ~163/101/12, crocus purple
~96/50/92). Each shape carries a height (midrib ridge, cupped petals) from which the tangent-space normal map is
taken. RGB is dilated into transparent texels so mips never pick up a halo. Usage: make_atlas.py <id>"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SID = sys.argv[1]
OUT = os.path.join(HERE, 'work', SID); os.makedirs(OUT, exist_ok=True)
SS = 4                      # supersampling
CELL = 256 * SS
rng = np.random.default_rng({'6flower02': 1234, '6flower07': 4321, '6flower06': 5611, '6flower08': 5812}[SID])
color = np.zeros((2 * CELL, 2 * CELL, 3), np.float32)
alpha = np.zeros((2 * CELL, 2 * CELL), np.float32)
height = np.zeros((2 * CELL, 2 * CELL), np.float32)


def stamp(cell, points, rgb_top, rgb_base, ridge=0.0, cup=0.0, shade=None):
    """Paint polygon `points` (cell-local, 0..1, v down) over the cell, back to front. Colour blends base->top along
    the polygon's own vertical extent; ridge raises the polygon's central spine, cup its middle."""
    cx, cy = cell % 2, cell // 2
    pts = [((cx + x) * CELL, (cy + y) * CELL) for x, y in points]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    # Clipped to the shape's own cell: neighbouring cells stay clean.
    x0, x1 = int(max(min(xs) - 2, cx * CELL)), int(min(max(xs) + 2, (cx + 1) * CELL))
    y0, y1 = int(max(min(ys) - 2, cy * CELL)), int(min(max(ys) + 2, (cy + 1) * CELL))
    if x1 <= x0 or y1 <= y0:
        return
    mask_image = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask_image).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
    mask = np.asarray(mask_image, np.float32) / 255.0
    if mask.max() == 0:
        return
    yy = np.linspace(0, 1, y1 - y0)[:, None] * np.ones((1, x1 - x0))
    rgb = np.array(rgb_base, np.float32)[None, None] * (1 - yy[..., None]) + np.array(rgb_top, np.float32)[None, None] * yy[..., None]
    rgb = rgb[::-1] if shade is None else rgb      # top of the bbox gets rgb_top
    distance = ndimage.distance_transform_edt(mask > 0.5)
    dmax = max(distance.max(), 1.0)
    h = 0.4 + ridge * (distance / dmax) + cup * (1 - (distance / dmax - 0.5) ** 2 * 4)
    region = (slice(y0, y1), slice(x0, x1))
    color[region] = color[region] * (1 - mask[..., None]) + rgb * mask[..., None]
    alpha[region] = np.maximum(alpha[region], mask)
    height[region] = height[region] * (1 - mask) + h * mask


def leaf(cell, base, angle, length, width, bend, rgb_top, rgb_base, ridge=0.6, steps=12, pointed=True):
    """Lanceolate leaf from base (cell-local) along angle (radians, 0 = up), curving by `bend`."""
    left, right = [], []
    for k in range(steps + 1):
        t = k / steps
        a = angle + bend * t
        if k == 0:
            px, py = base
        else:
            px += math.sin(a_prev) * length / steps; py -= math.cos(a_prev) * length / steps
        a_prev = a
        w = width * (math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.7) * (1 - 0.35 * t) if pointed else width * (1 - 0.6 * t)
        nx, ny = math.cos(a), math.sin(a)
        left.append((px - nx * w * 0.5, py - ny * w * 0.5)); right.append((px + nx * w * 0.5, py + ny * w * 0.5))
    stamp(cell, left + right[::-1], rgb_top, rgb_base, ridge=ridge)


def jitter(rgb, amount):
    return [min(max(c * (1 + rng.uniform(-amount, amount)), 0.0), 1.0) for c in rgb]


def foliage_gazania(cell):
    """Dense dome: leaves start inside the dome and point away from its centre (low ones outward, high ones up)."""
    for k in range(150):
        u = rng.uniform(-1, 1); v = rng.uniform()
        bx = 0.5 + u * 0.38 * (1 - 0.55 * v); by = 0.98 - v * 0.52
        angle = math.atan2(bx - 0.5, (0.98 - by) + 0.25) + rng.normal(0, 0.25)
        length = rng.uniform(0.12, 0.24); width = rng.uniform(0.05, 0.085)
        grey = rng.uniform(0.85, 1.2); depth = 0.75 + 0.5 * v       # higher leaves are later, lighter
        leaf(cell, (bx, by), angle, length, width, rng.normal(0, 0.3),
             jitter([0.31 * grey * depth, 0.46 * grey * depth, 0.19 * grey * depth], 0.06),
             jitter([0.08 * depth, 0.15 * depth, 0.05 * depth], 0.1), ridge=0.7)


def stem_strip(cell, top, base):
    stamp(cell, [(0.02, 0.0), (0.08, 0.0), (0.08, 1.0), (0.02, 1.0)], top, base, ridge=0.5)


def foliage_crocus(cell):
    for k in range(34):
        side = rng.uniform(-1, 1)
        angle = side * 0.75 + rng.normal(0, 0.08)
        base = (0.5 + rng.normal(0, 0.05), 1.0)
        length = rng.uniform(0.6, 0.95) * (1 - 0.25 * abs(side))
        leaf(cell, base, angle, length, rng.uniform(0.035, 0.05), side * 0.35 + rng.normal(0, 0.12),
             jitter([0.30, 0.46, 0.20], 0.08), jitter([0.10, 0.18, 0.07], 0.1), ridge=0.9, steps=14)
        # pale mid stripe
        leaf(cell, base, angle, length * 0.95, 0.008, side * 0.35, [0.62, 0.70, 0.52], [0.35, 0.42, 0.28], ridge=0.2,
             steps=14)


def gazania_head(cell, centre=(0.5, 0.5), radius=0.46, open_=1.0, tilt=1.0):
    cx, cy = centre
    rays = 17
    for k in range(rays):
        a = k / rays * 2 * math.pi + rng.normal(0, 0.05)
        length = radius * rng.uniform(0.88, 1.0)
        w = radius * 0.24
        pts = []
        for s in np.linspace(0, 1, 9):
            r = length * s; ww = w * math.sin(math.pi * min(s * 1.1 + 0.08, 1.0)) ** 0.6 * (1 - 0.25 * s)
            pts.append((r, ww))
        outline_ = [(p[0], -p[1]) for p in pts] + [(p[0], p[1]) for p in pts[::-1]]
        ca, sa = math.cos(a), math.sin(a)
        poly = [(cx + (r * ca - q * sa) * tilt, cy + (r * sa + q * ca) * open_) for r, q in outline_]
        stamp(cell, poly, jitter([1.0, 0.80, 0.16], 0.04), jitter([0.93, 0.50, 0.04], 0.06), cup=0.3)
        # thin dark ray at the petal's root, as on gazania
        stamp(cell, [(cx + (r * ca - q * sa) * tilt, cy + (r * sa + q * ca) * open_) for r, q in
                     ((radius * 0.28, -w * 0.12), (radius * 0.55, 0.0), (radius * 0.28, w * 0.12))],
              [0.45, 0.16, 0.03], [0.30, 0.10, 0.02])
    # dark zone ring with pale spots, then the disc
    ring = [(cx + math.cos(t) * radius * 0.30 * tilt, cy + math.sin(t) * radius * 0.30 * open_) for t in np.linspace(0, 2 * math.pi, 40)]
    stamp(cell, ring, [0.22, 0.10, 0.03], [0.30, 0.14, 0.04], cup=0.2)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        sx, sy = cx + math.cos(a) * radius * 0.24 * tilt, cy + math.sin(a) * radius * 0.24 * open_
        spot = [(sx + math.cos(t) * radius * 0.03, sy + math.sin(t) * radius * 0.03 * open_) for t in np.linspace(0, 2 * math.pi, 10)]
        stamp(cell, spot, [0.92, 0.86, 0.70], [0.92, 0.86, 0.70])
    disc = [(cx + math.cos(t) * radius * 0.16 * tilt, cy + math.sin(t) * radius * 0.16 * open_) for t in np.linspace(0, 2 * math.pi, 30)]
    stamp(cell, disc, [0.62, 0.42, 0.10], [0.45, 0.28, 0.06], cup=-0.3)


def crocus_petals(cell):
    """Six petals side by side across the cell (tileable: the lathe wraps u round the bloom), v up."""
    stamp(cell, [(0.0, 0.62), (1.0, 0.62), (1.0, 1.0), (0.0, 1.0)], [0.30, 0.16, 0.40], [0.78, 0.82, 0.62], ridge=0.0)
    for k in range(7):
        cx = k / 6.0
        pts = []
        for s in np.linspace(0, 1, 13):
            y = 1.0 - s * 0.97
            w = (1 / 6) * 0.62 * (math.sin(math.pi * (0.12 + 0.88 * s)) ** 0.45)
            pts.append((cx, y, w))
        outline_ = [(x - w, y) for x, y, w in pts] + [(x + w, y) for x, y, w in pts[::-1]]
        bright = 0.9 + 0.2 * rng.uniform()
        stamp(cell, outline_, jitter([0.52 * bright, 0.26 * bright, 0.66 * bright], 0.04), jitter([0.18, 0.06, 0.26], 0.08),
              cup=0.6)
        for dx in (-0.025, 0.0, 0.025):     # darker veins up each petal
            stamp(cell, [(cx + dx - 0.003, 0.95), (cx + dx + 0.003, 0.95), (cx + dx * 0.4 + 0.002, 0.25),
                         (cx + dx * 0.4 - 0.002, 0.25)], [0.34, 0.15, 0.46], [0.24, 0.09, 0.32])


def crocus_centre(cell):
    stamp(cell, [(0.5 + math.cos(t) * 0.30, 0.5 + math.sin(t) * 0.30) for t in np.linspace(0, 2 * math.pi, 30)],
          [0.32, 0.13, 0.44], [0.24, 0.08, 0.32], cup=-0.4)
    for k in range(3):
        a = k / 3 * 2 * math.pi
        stamp(cell, [(0.5 + math.cos(a + d) * r, 0.5 + math.sin(a + d) * r) for d, r in
                     ((0.0, 0.0), (-0.22, 0.17), (0.0, 0.26), (0.22, 0.17))], [1.0, 0.74, 0.14], [0.95, 0.55, 0.05])
    stem_strip(cell, [0.56, 0.62, 0.44], [0.36, 0.44, 0.26])


def rose_bloom(cell, centre, radius, deep=False):
    """Pink-red rose seen face on: three rings of rounded petals (outer light, inner darker), a dark red spiral core."""
    cx, cy = centre
    outer = [0.86, 0.22, 0.34] if deep else [0.97, 0.40, 0.52]
    inner = [0.58, 0.07, 0.15] if deep else [0.80, 0.16, 0.28]
    for ring, (count, r0, w) in enumerate(((7, 0.62, 0.42), (6, 0.42, 0.36), (5, 0.24, 0.30))):
        turn = rng.uniform(0, 2 * math.pi)
        for k in range(count):
            a = turn + 2 * math.pi * k / count
            px, py = cx + math.cos(a) * radius * r0, cy + math.sin(a) * radius * r0
            pts = [(px + math.cos(t) * radius * w, py + math.sin(t) * radius * w * 0.85) for t in np.linspace(0, 2 * math.pi, 14)]
            mix = ring / 2
            stamp(cell, pts, jitter([o * (1 - mix) + i * mix for o, i in zip(outer, inner)], 0.05),
                  jitter([i * 0.8 for i in inner], 0.05), cup=0.5)
    for k in range(10):                          # spiral heart
        t = k / 10
        a = t * 4 * math.pi; r = radius * 0.18 * (1 - t)
        stamp(cell, [(cx + math.cos(a) * r + math.cos(q) * radius * 0.07, cy + math.sin(a) * r + math.sin(q) * radius * 0.06)
                     for q in np.linspace(0, 2 * math.pi, 10)], [i * 0.55 for i in inner], [i * 0.35 for i in inner], cup=0.3)


def foliage_rose(cell):
    """Dense rose bush: many small dark oval leaflets in sprays, and small pink-red roses painted in for distance."""
    for k in range(950):
        bx, by = rng.uniform(0.06, 0.94), rng.uniform(0.08, 0.98)
        if (bx - 0.5) ** 2 / 0.22 + (by - 0.58) ** 2 / 0.20 > 1.0:
            continue
        depth = 0.7 + 0.6 * (1 - by)                # leaves higher on the card are lighter (sunlit top)
        lit = 1.8 if rng.uniform() < 0.16 else 1.15  # scattered sunlit leaves, as on the sprite
        leaf(cell, (bx, by), rng.uniform(-1.2, 1.2), rng.uniform(0.07, 0.12), rng.uniform(0.045, 0.07),
             rng.normal(0, 0.25), jitter([0.10 * depth * lit, 0.27 * depth * lit, 0.07 * depth * lit], 0.12),
             jitter([0.02, 0.09, 0.02], 0.15), ridge=0.6, steps=8)
    for k in range(26):                             # sprays of leaflets breaking the clump's round outline
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.36, 0.42)
        x, y = 0.5 + math.cos(a) * r * 1.05, 0.58 + math.sin(a) * r
        for step in range(int(rng.integers(3, 6))):
            x += math.cos(a) * 0.035; y += math.sin(a) * 0.035
            if not (0.03 < x < 0.97 and 0.03 < y < 0.99):
                break
            for side in (-1, 1):
                leaf(cell, (x, y), math.atan2(math.cos(a), -math.sin(a)) + side * 0.9 + rng.normal(0, 0.2),
                     rng.uniform(0.06, 0.09), rng.uniform(0.04, 0.055), rng.normal(0, 0.2),
                     jitter([0.14, 0.33, 0.09], 0.12), jitter([0.03, 0.10, 0.02], 0.15), ridge=0.6, steps=8)
    for k in range(10):
        bx, by = rng.uniform(0.15, 0.85), rng.uniform(0.18, 0.92)
        if (bx - 0.5) ** 2 / 0.20 + (by - 0.58) ** 2 / 0.18 > 1.0:
            continue
        rose_bloom(cell, (bx, by), rng.uniform(0.045, 0.06), deep=rng.uniform() < 0.35)


def foliage_sunflower(cell):
    """Broad rough heart-shaped leaves on short stalks, rising from the bottom of the card."""
    for k in range(46):
        side = rng.uniform(-1, 1)
        base = (0.5 + side * 0.22 + rng.normal(0, 0.04), rng.uniform(0.78, 1.0))
        angle = side * 0.9 + rng.normal(0, 0.2)
        depth = 0.8 + 0.4 * rng.uniform()
        leaf(cell, base, angle, rng.uniform(0.32, 0.50), rng.uniform(0.18, 0.26), side * 0.4 + rng.normal(0, 0.15),
             jitter([0.30 * depth, 0.44 * depth, 0.15 * depth], 0.08), jitter([0.10, 0.18, 0.05], 0.1), ridge=0.8,
             steps=10, pointed=True)


def sunflower_head(cell, centre=(0.5, 0.5), radius=0.47):
    """Golden rays round a large dark seed disc with a lighter ring of florets."""
    cx, cy = centre
    for layer, (rays, offset, scale) in enumerate(((22, 0.0, 1.0), (22, 0.5, 0.86))):
        for k in range(rays):
            a = (k + offset) / rays * 2 * math.pi + rng.normal(0, 0.04)
            length = radius * scale * rng.uniform(0.9, 1.0); w = radius * 0.16
            pts = []
            for t in np.linspace(0, 1, 9):
                r = radius * 0.34 + (length - radius * 0.34) * t
                ww = w * math.sin(math.pi * min(t * 1.05 + 0.1, 1.0)) ** 0.5 * (1 - 0.4 * t)
                pts.append((r, ww))
            outline_ = [(r, -q) for r, q in pts] + [(r, q) for r, q in pts[::-1]]
            ca, sa = math.cos(a), math.sin(a)
            light = 1.0 - 0.12 * layer
            stamp(cell, [(cx + r * ca - q * sa, cy + r * sa + q * ca) for r, q in outline_],
                  jitter([1.0 * light, 0.78 * light, 0.14 * light], 0.04), jitter([0.88, 0.52, 0.05], 0.05), cup=0.3)
    disc = [(cx + math.cos(t) * radius * 0.38, cy + math.sin(t) * radius * 0.38) for t in np.linspace(0, 2 * math.pi, 40)]
    stamp(cell, disc, [0.42, 0.24, 0.06], [0.30, 0.16, 0.04], cup=0.2)
    inner = [(cx + math.cos(t) * radius * 0.30, cy + math.sin(t) * radius * 0.30) for t in np.linspace(0, 2 * math.pi, 40)]
    stamp(cell, inner, [0.20, 0.10, 0.03], [0.14, 0.07, 0.02], cup=-0.2)
    for k in range(70):                            # seed dots
        r = radius * 0.28 * math.sqrt(rng.uniform()); a = rng.uniform(0, 2 * math.pi)
        sx, sy = cx + math.cos(a) * r, cy + math.sin(a) * r
        stamp(cell, [(sx + math.cos(t) * radius * 0.018, sy + math.sin(t) * radius * 0.018) for t in np.linspace(0, 2 * math.pi, 7)],
              [0.34, 0.20, 0.06], [0.34, 0.20, 0.06])


if SID == '6flower02':
    foliage_gazania(0); foliage_gazania(1); gazania_head(2); stem_strip(3, [0.30, 0.42, 0.22], [0.16, 0.25, 0.10])
elif SID == '6flower07':
    foliage_crocus(0); foliage_crocus(1); crocus_petals(2); crocus_centre(3)
elif SID == '6flower06':
    foliage_rose(0); foliage_rose(1); rose_bloom(2, (0.5, 0.5), 0.40); stem_strip(3, [0.16, 0.30, 0.10], [0.08, 0.16, 0.05])
else:
    foliage_sunflower(0); foliage_sunflower(1); sunflower_head(2); stem_strip(3, [0.32, 0.46, 0.18], [0.16, 0.26, 0.08])

# downsample (premultiplied), normal from height, dilate colour into transparent texels
def down(a):
    return np.asarray(Image.fromarray(a.astype(np.float32)).resize((512, 512), Image.BOX))

premult = [down(color[..., c] * alpha) for c in range(3)]
a = down(alpha)
rgb = np.stack([p / np.maximum(a, 1e-4) for p in premult], -1)
h = down(height * alpha)
gy, gx = np.gradient(ndimage.gaussian_filter(h, 0.8))
n = np.stack([-gx * 6.0, gy * 6.0, np.ones_like(h)], -1)          # image rows go down: green = up
n /= np.linalg.norm(n, axis=-1, keepdims=True)
covered = a > 0.02
_, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
rgb = rgb[iy, ix]; nrm = n[iy, ix]
rgb = np.clip(rgb, 0, 1)
Image.fromarray(np.dstack([(rgb * 255 + 0.5).astype(np.uint8), (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)]), 'RGBA').save(
    os.path.join(OUT, 'atlas_basecolor.png'))
Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'atlas_normal.png'))
cells = [(a[r * 256:(r + 1) * 256, c * 256:(c + 1) * 256] >= 0.5).mean() for r in (0, 1) for c in (0, 1)]
print('ATLAS', SID, 'cell coverage', [round(float(x), 2) for x in cells])
