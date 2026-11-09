#!/usr/bin/env python3
"""Shared texture set of the four meadow bushes (textures/):

- leaves_basecolor.png (1024 RGBA, alpha cut-out) and leaves_normal.png (1024, OpenGL +Y): four 512 px cells, each one
  card's worth of foliage, laid out like the tree atlases (cell k: row k // 2, column k % 2):
    0 small-leaved dense spray (box, hawthorn): 11-13 twigs, 3-4 cm leaves at 0.4 m per card
    1 the same with lighter, yellower young growth at the twig ends
    2 broadleaf clump (bramble, elder): compound leaves of three or five wide leaflets, 8-12 cm at 0.5 m per card
    3 open medium spray (sapling crown): 7-8 twigs of 5-6 cm leaves with gaps between them
  Leaves are cut from ambientCG LeafSet022 (CC0), the source of every tree leaf atlas in the project
  (../mm6_new_sorpigal_3d/trees/source/leafset022); the two leaves with the worst brown blotches are left out. Each
  leaf keeps its own tangent normal, rotated with it, plus a fold across its width, as in the tree atlases
  (../mm7_3d/trees_a/scripts/make_leaf_atlas.py, whose spray approach this follows). No crown occlusion is baked here:
  it is the COLOR_0 vertex colour. RGB and normals are dilated into the transparent texels (no halo at mips).
- bark_basecolor.png and bark_normal.png (512): Poly Haven bark_brown_01 (CC0, the trees' bark), diffuse x AO^1.5,
  graded to a grey-brown shrub stem, OpenGL normal.

Colours: leaf albedo is a natural mid green (sRGB ~100/156/72 before per-leaf variation; base colour kept within
sRGB 30-243). The game tints bushes per instance. Usage: make_textures.py"""
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SOURCE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'trees', 'source')
OUT = os.path.join(HERE, 'textures')
CELL = 512

lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)

# ---------------------------------------------------------------- leaves from LeafSet022
leafset = os.path.join(SOURCE, 'leafset022')
colour = np.asarray(Image.open(os.path.join(leafset, 'LeafSet022_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
opacity = np.asarray(Image.open(os.path.join(leafset, 'LeafSet022_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
normal = np.asarray(Image.open(os.path.join(leafset, 'LeafSet022_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
labels, _ = ndimage.label(opacity > 0.5)
leaves = []
for sl in ndimage.find_objects(labels):
    if sl[0].stop - sl[0].start < 100:
        continue
    pad = 6
    ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
    c, a = colour[ys, xs], opacity[ys, xs]
    lum = c.mean(-1)[a > 0.5]
    blotch = float((lum < 0.6 * np.median(lum)).mean())        # brown spots and dead tips
    leaves.append((blotch, c, a, normal[ys, xs]))
leaves.sort(key=lambda entry: entry[0])
print('LEAVES blotch fractions', [round(entry[0], 3) for entry in leaves])
leaves = [entry[1:] for entry in leaves[:-2]]               # drop the two most blotched leaves
MEAN = np.mean([lin(c)[a > 0.5].mean(0) for c, a, _ in leaves], 0)


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


class Canvas:
    def __init__(self):
        self.c = np.zeros((CELL, CELL, 3), np.float32)
        self.a = np.zeros((CELL, CELL), np.float32)
        self.n = np.zeros((CELL, CELL, 3), np.float32); self.n[...] = (0.5, 0.5, 1.0)
        self.yy, self.xx = np.mgrid[:CELL, :CELL]
        self.placed = 0

    def twig(self, path, width, rgb, skip=0.0):
        """A twig along path (pixel points), tapering toward its end; the first `skip` of it is not drawn (no dark
        star at the hub when a card is seen from below)."""
        for i, (tx, ty) in enumerate(path):
            if i < skip * len(path):
                continue
            w = width * (1 - i / len(path)) + 0.6
            m = (self.xx - tx) ** 2 + (self.yy - ty) ** 2 < w * w
            self.c[m] = rgb; self.a[m] = 1.0

    def leaf(self, r, bx, by, angle_deg, length_px, value, target, width_scale=1.0, jitter=(0.88, 1.12)):
        """One leaf with its stalk end at (bx, by), its tip toward screen angle angle_deg (0 = up, clockwise)."""
        c, a, nm = leaves[r.integers(len(leaves))]
        s = length_px / c.shape[0]
        hgt, wid = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s * width_scale), 3)
        c, a, nm = resize(c, wid, hgt), resize(a, wid, hgt), resize(nm, wid, hgt)
        x = (np.arange(wid) - (wid - 1) / 2) / max(wid / 2, 1)
        fold = np.clip(x, -1, 1)[None, :] * math.sin(math.radians(25)) * r.choice([-1.0, 1.0])
        n = nm * 2 - 1
        n[..., 0] = n[..., 0] + fold
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)
        cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
        aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
        nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
        th = math.radians(-angle_deg)
        nx, ny = nR[..., 0], -nR[..., 1]
        rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
        nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
        cl = lin(np.clip(cR, 0, 1)) / MEAN * target * value
        cl *= np.array([r.uniform(*jitter), 1.0, r.uniform(0.85, 1.1)])
        hh, ww = aR.shape
        ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
        ys_, xs_ = np.nonzero(aR > 0.05)
        if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 \
                or ox + xs_.max() >= CELL - 8:
            return False
        x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, CELL), min(oy + hh, CELL)
        sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
        av = np.clip(aR[sub], 0, 1)[..., None]
        region = (slice(y0, y1), slice(x0, x1))
        self.c[region] = self.c[region] * (1 - av) + srgb(cl[sub]) * av
        self.n[region] = self.n[region] * (1 - av) + nR[sub] * av
        self.a[region] = np.maximum(self.a[region], av[..., 0])
        self.placed += 1
        return True


def fill_gaps(cv, r, origin, radius, length, target, width_scale=1.0, tries=12):
    """Cover transparent holes near the centre: a leaf from the hole's centre outward, until none is left."""
    for _ in range(tries):
        hole = (cv.a < 0.5) & ((cv.xx - origin[0]) ** 2 + (cv.yy - origin[1]) ** 2 < radius ** 2)
        lab, count = ndimage.label(hole)
        if count == 0:
            return
        sizes = ndimage.sum(hole, lab, range(1, count + 1))
        k = int(np.argmax(sizes))
        if sizes[k] < 40:
            return
        cy, cx = ndimage.center_of_mass(hole, lab, k + 1)
        out = math.degrees(math.atan2(cx - origin[0], -(cy - origin[1]))) + r.uniform(-30, 30)
        start = np.array([cx, cy]) - 0.35 * length[0] * heading_vector(out)
        cv.leaf(r, start[0], start[1], out, r.uniform(*length), r.uniform(0.9, 1.1), target, width_scale)


def heading_vector(deg):
    return np.array([math.sin(math.radians(deg)), -math.cos(math.radians(deg))])


def walk(r, origin, heading, steps, step_px=2.0, wobble=0.03):
    p = origin.astype(float).copy(); ang = math.radians(heading); path = []
    for _ in range(steps):
        path.append(p.copy()); p = p + step_px * np.array([math.sin(ang), -math.cos(ang)])
        ang += r.uniform(-wobble, wobble)
    return path


GREEN = lin(np.array([100.0, 156.0, 72.0]) / 255)
YOUNG = lin(np.array([128.0, 172.0, 70.0]) / 255)
BROAD = lin(np.array([92.0, 150.0, 70.0]) / 255)
TWIG = (0.22, 0.18, 0.11)


def small_spray(seed, young=0.0):
    """Dense small-leaved spray: many short twigs, alternate 3-4 cm leaves, more leaves over the hub."""
    r = np.random.default_rng(seed); cv = Canvas()
    origin = np.array([CELL / 2, CELL / 2]) + r.uniform(-10, 10, 2)
    twigs = int(r.integers(11, 14))
    for heading in np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-12, 12, twigs):
        steps = int(r.uniform(85, 110)); path = walk(r, origin, heading, steps)
        cv.twig(path, 1.3, TWIG, skip=0.3)
        count = int(r.integers(12, 16))
        for k in range(count):
            f = 0.2 + 0.78 * (k + r.uniform(-0.25, 0.25)) / count
            tx, ty = path[min(int(f * steps), steps - 1)]
            side = 1 if k % 2 == 0 else -1
            tgt = YOUNG if young and f > 0.75 and r.random() < young else GREEN
            value = r.uniform(0.8, 1.2) * (0.78 + 0.22 * f)
            cv.leaf(r, tx, ty, heading + side * r.uniform(35, 65), r.uniform(38, 50), value, tgt, 1.1)
        tx, ty = path[-1]
        cv.leaf(r, tx, ty, heading + r.uniform(-12, 12), r.uniform(42, 52), r.uniform(0.95, 1.2),
                YOUNG if young else GREEN, 1.1)
    for _ in range(int(r.integers(30, 40))):                  # fill over the hub and between the twigs
        heading = r.uniform(0, 360); d = r.uniform(0, 150)
        tx, ty = origin + d * heading_vector(heading)
        cv.leaf(r, tx, ty, heading + r.uniform(-40, 40), r.uniform(38, 48), r.uniform(0.85, 1.1), GREEN, 1.1)
    fill_gaps(cv, r, origin, 110, (38, 48), GREEN, 1.1, tries=20)
    return cv


def broad_clump(seed):
    """Broadleaf clump: compound leaves (three or five wide leaflets on a short stalk) radiating from the centre,
    the outer ones first and the central ones on top."""
    r = np.random.default_rng(seed); cv = Canvas()
    origin = np.array([CELL / 2, CELL / 2]) + r.uniform(-8, 8, 2)
    leaves_ = int(r.integers(13, 16))
    order = np.linspace(0, 360, leaves_, endpoint=False) + r.uniform(0, 360) + r.uniform(-15, 15, leaves_)
    for k, heading in enumerate(order):
        outer = k < leaves_ - 3
        reach = r.uniform(40, 95) if outer else r.uniform(15, 35)
        stalk = walk(r, origin, heading, int(reach / 2))
        cv.twig(stalk, 1.6, (0.25, 0.24, 0.12), skip=0.35)
        bx, by = stalk[-1]
        leaflets = 5 if r.random() < 0.55 else 3
        fan = (-62, -32, 0, 32, 62) if leaflets == 5 else (-40, 0, 40)
        value = r.uniform(0.82, 1.15) * (0.85 if outer else 1.0)
        for j, spread in enumerate(fan):
            length = r.uniform(92, 118) * (1.0 if spread == 0 else 0.86 if abs(spread) < 50 else 0.7)
            cv.leaf(r, bx, by, heading + spread + r.uniform(-6, 6), length, value * r.uniform(0.93, 1.07), BROAD,
                    1.2, jitter=(0.9, 1.08))
    hub = np.random.default_rng(seed + 1000)                  # leaflets lying across the centre, on top
    for _ in range(10):
        heading = hub.uniform(0, 360)
        bx, by = origin - hub.uniform(30, 60) * heading_vector(heading)
        cv.leaf(hub, bx, by, heading, hub.uniform(88, 104), hub.uniform(0.95, 1.12), BROAD, 1.2, jitter=(0.9, 1.08))
    fill_gaps(cv, hub, origin, 120, (80, 96), BROAD, 1.2)
    return cv


def open_spray(seed):
    """Open medium spray for the sapling crown: fewer twigs, 5-6 cm leaves, gaps between the twigs."""
    r = np.random.default_rng(seed); cv = Canvas()
    origin = np.array([CELL / 2, CELL / 2]) + r.uniform(-12, 12, 2)
    twigs = int(r.integers(7, 9))
    for heading in np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-15, 15, twigs):
        steps = int(r.uniform(85, 105)); path = walk(r, origin, heading, steps)
        cv.twig(path, 1.6, TWIG, skip=0.3)
        count = int(r.integers(7, 10))
        for k in range(count):
            f = 0.3 + 0.68 * (k + r.uniform(-0.2, 0.2)) / count
            tx, ty = path[min(int(f * steps), steps - 1)]
            side = 1 if k % 2 == 0 else -1
            value = r.uniform(0.82, 1.2) * (0.8 + 0.2 * f)
            cv.leaf(r, tx, ty, heading + side * r.uniform(30, 55), r.uniform(58, 72), value, GREEN)
        tx, ty = path[-1]
        cv.leaf(r, tx, ty, heading + r.uniform(-10, 10), r.uniform(62, 74), r.uniform(0.95, 1.15), GREEN)
    for _ in range(int(r.integers(6, 9))):
        heading = r.uniform(0, 360); d = r.uniform(5, 50)
        tx, ty = origin + d * heading_vector(heading)
        cv.leaf(r, tx, ty, heading, r.uniform(56, 68), r.uniform(0.9, 1.1), GREEN)
    return cv


cells = [small_spray(5101), small_spray(5113, young=0.6), broad_clump(5127), open_spray(5139)]
base = np.zeros((1024, 1024, 4), np.float32); nrm = np.zeros((1024, 1024, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
info = []
for k, cv in enumerate(cells):
    border = np.zeros_like(cv.a); border[6:-6, 6:-6] = 1
    row, col = divmod(k, 2)
    sl = (slice(row * CELL, (row + 1) * CELL), slice(col * CELL, (col + 1) * CELL))
    base[sl[0], sl[1], :3] = np.clip(cv.c, 30 / 255, 243 / 255)
    base[sl[0], sl[1], 3] = cv.a * border
    nrm[sl] = cv.n
    inside = cv.a * border > 0.5
    info.append((cv.placed, round(float(inside.mean()), 3), (np.clip(cv.c, 0, 1)[inside].mean(0) * 255).round().tolist()))
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).round().astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).round().astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
preview = Image.new('RGBA', (1024, 1024), (150, 160, 175, 255))
preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
preview.convert('RGB').save(os.path.join(HERE, 'review', 'atlas_preview.png'))
print('ATLAS cells (leaves, coverage, mean sRGB)', info)

# ---------------------------------------------------------------- bark
bark = os.path.join(SOURCE, 'bark_brown_01')


def load(name):
    raw = np.asarray(Image.open(os.path.join(bark, f'bark_brown_01_{name}_2k.png')))
    values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
    return values[..., :3] if values.ndim == 3 else values


diffuse, ao = lin(load('diff')), load('ao')
ao = ao.mean(-1) if ao.ndim == 3 else ao
albedo = diffuse * (ao ** 1.5)[..., None]
target = lin(np.array([88.0, 74.0, 60.0]) / 255)
albedo = albedo / albedo.reshape(-1, 3).mean(0) * target
bark_rgb = np.clip(srgb(albedo), 30 / 255, 243 / 255)
Image.fromarray((bark_rgb * 255).round().astype(np.uint8), 'RGB').resize((512, 512), Image.LANCZOS) \
    .save(os.path.join(OUT, 'bark_basecolor.png'))
Image.fromarray((np.clip(load('nor_gl'), 0, 1) * 255).round().astype(np.uint8), 'RGB').resize((512, 512), Image.LANCZOS) \
    .save(os.path.join(OUT, 'bark_normal.png'))
print('BARK mean sRGB', (bark_rgb.reshape(-1, 3).mean(0) * 255).round().tolist())
