#!/usr/bin/env python3
"""Shared textures of the MM8 trees_other batch (shared/), embedded byte-identical in every GLB so the cooker stores
them once (tools/cook_models.py keys textures by content). Species colour comes from COLOR_0 (common.tints()).

 - bark: bark_basecolor.png / bark_normal.png / bark_mr.png (1024): Poly Haven bark_brown_01 (CC0) as in the MM6
   trees (diffuse x AO^1.5 x a little height), graded to a light neutral brown BARK_SRGB; bark.json its mean.
 - needles: needles_basecolor.png (2048 RGBA) / needles_normal.png, procedural conifer foliage (needles.json: per cell
   its uv rectangle, alpha-weighted mean linear colour and coverage):
     cells 0-3   fronds, 512 x 1024 (image rows 0-1023): one flat feathery branch spray with its stem along the cell
                 (base at the bottom, tip at the top): alternate side branchlets, each with a few sub-branchlets,
                 needles along both sides of every twig (two half-strips with tilted normals), darker toward the
                 stem, lighter yellow-green toward the tips, a few reddish buds at branchlet tips (tree29/tree30);
     cells 4-7   spray clusters, 512 x 512 (rows 1024-1535): 6-9 small fronds radiating from a hub, for clump cards
                 of a pad (tree16);
     cells 8-11  the same clusters with some fronds yellow-olive (rows 1536-2047).
 - leaves: see make_leaf_shared.py (separate, the broadleaf species).
Drawn at 2x and box-filtered; RGB/normals dilated into transparent texels. Usage: make_shared.py [bark|needles]..."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import common

OUT = common.SHARED
os.makedirs(OUT, exist_ok=True)
lin, srgb = common.lin, common.srgb
parts = sys.argv[1:] or ['bark', 'needles']

# ---------------------------------------------------------------- bark
BARK_SRGB = [176, 156, 138]


def make_bark():
    S = os.path.join(common.SOURCE, 'bark_brown_01')

    def load(name, channels):
        raw = np.asarray(Image.open(os.path.join(S, f'bark_brown_01_{name}_2k.png')))
        values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
        return values[..., :channels] if values.ndim == 3 else values

    diffuse = lin(load('diff', 3))
    ao = load('ao', 1)
    height = load('disp', 3).mean(2)
    height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
    bark = diffuse * (ao ** 1.5 * (0.7 + 0.3 * height))[..., None]
    bark = bark / bark.reshape(-1, 3).mean(0) * lin(np.array(BARK_SRGB) / 255.0)
    size = (1024, 1024)
    img = Image.fromarray((np.clip(srgb(bark), 0, 1) * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    img.save(os.path.join(OUT, 'bark_basecolor.png'))
    Image.open(os.path.join(S, 'bark_brown_01_nor_gl_2k.png')).convert('RGB').resize(size, Image.LANCZOS).save(
        os.path.join(OUT, 'bark_normal.png'))
    rough = (load('rough', 1) * 255).astype(np.uint8); zero = np.zeros_like(rough)
    Image.fromarray(np.stack([zero, rough, zero], 2)).resize(size, Image.LANCZOS).save(os.path.join(OUT, 'bark_mr.png'))
    mean = lin(np.asarray(img, np.float32) / 255).reshape(-1, 3).mean(0)
    json.dump({'mean_linear': mean.round(5).tolist(), 'srgb': BARK_SRGB}, open(os.path.join(OUT, 'bark.json'), 'w'))
    print('BARK mean linear', mean.round(4))


# ---------------------------------------------------------------- needles
NEEDLE_SRGB = np.array([164, 184, 70])          # mean needle albedo (neutral-ish; species tint in COLOR_0)
YELLOW_SRGB = np.array([210, 190, 66])          # yellow-olive fronds of cells 8-11
TWIG_SRGB = np.array([92, 66, 46])
BUD_SRGB = np.array([150, 84, 74])
SS = 2                                          # supersampling


class Canvas:
    """2x RGB / normal / alpha layers of one cell, drawn with PIL lines."""

    def __init__(self, w, h):
        self.w, self.h = w * SS, h * SS
        self.c = Image.new('RGB', (self.w, self.h)); self.n = Image.new('RGB', (self.w, self.h), (128, 128, 255))
        self.a = Image.new('L', (self.w, self.h))
        self.dc, self.dn, self.da = ImageDraw.Draw(self.c), ImageDraw.Draw(self.n), ImageDraw.Draw(self.a)

    def line(self, pts, rgb_lin, width, normal=(0.0, 0.0, 1.0)):
        col = tuple(int(v) for v in (np.clip(srgb(np.clip(rgb_lin, 0, 1)), 0, 1) * 255).round())
        n = np.array(normal, float); n /= np.linalg.norm(n)
        nc = tuple(int(v) for v in ((n * 0.5 + 0.5) * 255).round())
        pts = [tuple(map(float, p)) for p in pts]
        w = max(int(round(width)), 1)
        self.dc.line(pts, fill=col, width=w); self.dn.line(pts, fill=nc, width=w); self.da.line(pts, fill=255, width=w)
        if w >= 4:
            for p in (pts[0], pts[-1]):
                r = w / 2
                box = (p[0] - r, p[1] - r, p[0] + r, p[1] + r)
                self.dc.ellipse(box, fill=col); self.dn.ellipse(box, fill=nc); self.da.ellipse(box, fill=255)

    def dot(self, p, r, rgb_lin):
        col = tuple(int(v) for v in (np.clip(srgb(np.clip(rgb_lin, 0, 1)), 0, 1) * 255).round())
        box = (p[0] - r, p[1] - r, p[0] + r, p[1] + r)
        self.dc.ellipse(box, fill=col); self.dn.ellipse(box, fill=(128, 128, 255)); self.da.ellipse(box, fill=255)

    def result(self, border=6):
        h, w = self.h // SS, self.w // SS
        a2 = np.asarray(self.a, np.float32) / 255
        c2 = np.asarray(self.c, np.float32) / 255; n2 = np.asarray(self.n, np.float32) / 255
        box = lambda x: x.reshape(h, SS, w, SS, *x.shape[2:]).mean((1, 3))
        a = box(a2)
        c = box(c2 * a2[..., None]) / np.maximum(a[..., None], 1e-6)
        n = box(n2 * a2[..., None]) / np.maximum(a[..., None], 1e-6)
        n = np.where(a[..., None] > 0, n, (0.5, 0.5, 1.0))
        mask = np.zeros_like(a); mask[border:-border, border:-border] = 1
        return c, a * mask, n


def unit(angle):
    """Image direction for a heading (0 = up, clockwise positive)."""
    return np.array([math.sin(angle), -math.cos(angle)])


def twig_path(start, heading, length, rng, bend=0.0, step=6.0, wander=0.02):
    steps = max(int(length / step), 2); p = np.array(start, float); ang = heading; path = [p.copy()]
    for _ in range(steps):
        p = p + step * unit(ang); ang += bend / steps + rng.uniform(-wander, wander); path.append(p.copy())
    return path


def needles_along(cv, path, rng, colour, side_sign, t_frond, needle_len, spacing, start_f=0.06):
    """Needles on both sides of a twig path (two half-strips each), lighter toward the twig tip."""
    travelled = 0.0; count = 0
    for i in range(1, len(path)):
        d = path[i] - path[i - 1]; seg = np.linalg.norm(d); travelled += seg
        if travelled < spacing:
            continue
        travelled = 0.0
        f = i / (len(path) - 1)
        if f < start_f:
            continue
        heading = math.atan2(d[0], -d[1])
        for side in (-1, 1):
            if rng.random() < 0.06:
                continue
            a = heading + side * math.radians(rng.uniform(42, 70))
            ln = rng.uniform(*needle_len) * (0.7 + 0.3 * (1 - f) + 0.1 * rng.random())
            dv = unit(a); perp = np.array([-dv[1], dv[0]])
            base = path[i]; tip = base + dv * ln
            value = rng.uniform(0.8, 1.18) * (0.62 + 0.5 * f) * (0.88 + 0.2 * t_frond)
            rgb = colour * value * np.array([rng.uniform(0.92, 1.08), 1.0, rng.uniform(0.85, 1.1)])
            if f > 0.82:                                   # fresh growth at the tips: lighter, yellower
                rgb = rgb * np.array([1.22, 1.15, 0.85])
            for half in (-1, 1):
                off = perp * half * 1.3
                nx, ny = perp * half * 0.55 + np.array([side_sign * 0.22, 0.0])
                cv.line([base + off, tip + off * 0.4], rgb * (1.0 + 0.12 * half), 2.6,
                        normal=(nx, -ny, 1.0))
            count += 1
    return count


def draw_frond(cv, base, heading, length, half_width, rng, colour, buds=0.55, needle_len=(26, 40), spacing=5.0):
    """One flat branch spray: stem from base toward heading, alternate branchlets forming a lanceolate outline whose
    half-width peaks at half_width (px), sub-branchlets, needles everywhere."""
    twig = lin(TWIG_SRGB / 255.0)
    phase = rng.uniform(0, 6.3); amp = rng.uniform(-0.12, 0.12)
    axis = twig_path(base, heading, length, rng, bend=amp, step=8.0, wander=0.003)
    for i in range(len(axis) - 1):
        t = i / (len(axis) - 1)
        cv.line([axis[i], axis[i + 1]], twig * (0.8 + 0.3 * t), max(26 * (1 - t) ** 0.8 * length / 1900 + 4, 5))
    total = 0
    t = rng.uniform(0.03, 0.06); side = rng.choice([-1, 1])
    branchlets = []
    while t < 0.97:
        i = min(int(t * (len(axis) - 1)), len(axis) - 2)
        d = axis[i + 1] - axis[i]; ah = math.atan2(d[0], -d[1])
        a = math.radians(rng.uniform(48, 64))
        shape = math.sin(math.pi * min(t / 0.98, 1.0) ** 0.85) ** 0.7 * (1 - 0.3 * t)
        ln = half_width / math.sin(a) * shape * rng.uniform(0.82, 1.08)
        branchlets.append((axis[i], ah + side * a, ln, side, t))
        t += rng.uniform(0.022, 0.034)
        side = -side if rng.random() > 0.15 else side
    for start, h, ln, s, tf in branchlets:
        if ln < 12:
            continue
        path = twig_path(start, h, ln, rng, bend=-s * rng.uniform(0.15, 0.35))
        cv.line(path, twig * 0.9, max(4.5 * (1 - tf) + 2, 2))
        subs = []
        if ln > 110:
            k = int(ln / 85)
            for j in range(k):
                f = (j + 1) / (k + 1) * rng.uniform(0.85, 1.1)
                i = min(int(f * (len(path) - 1)), len(path) - 2)
                d = path[i + 1] - path[i]; hh = math.atan2(d[0], -d[1])
                ss = 1 if j % 2 == 0 else -1
                subs.append(twig_path(path[i], hh + ss * math.radians(rng.uniform(42, 58)),
                                      ln * rng.uniform(0.25, 0.42) * (1 - 0.5 * f), rng, bend=-ss * 0.2))
        for sp in subs:
            cv.line(sp, twig * 0.9, 2)
        for sp in subs:
            total += needles_along(cv, sp, rng, colour, s, tf, needle_len, spacing)
        total += needles_along(cv, path, rng, colour, s, tf, needle_len, spacing, start_f=0.1)
        if rng.random() < buds:
            cv.dot(path[-1] + unit(h) * 5, rng.uniform(5.0, 8.0), lin(BUD_SRGB / 255.0) * rng.uniform(0.8, 1.15))
    # needles on the upper stem (the spray's leading tip)
    total += needles_along(cv, axis[int(0.75 * len(axis)):], rng, colour, 0, 1.0, needle_len, spacing)
    return total


def frond_cell(seed):
    rng = np.random.default_rng(seed)
    cv = Canvas(512, 1024)
    colour = lin(NEEDLE_SRGB / 255.0)
    base = np.array([cv.w / 2 + rng.uniform(-10, 10), cv.h - 20])
    n = draw_frond(cv, base, rng.uniform(-0.03, 0.03), cv.h - 70, cv.w / 2 - 40, rng, colour)
    c, a, nm = cv.result()
    return c, a, nm, n


def cluster_cell(seed, yellow=0.0):
    """A dense pad (tree16's foliage clouds): two layers of broad sprays radiating from the hub, the upper layer
    shorter and rotated half a step, plus short tufts over the hub."""
    rng = np.random.default_rng(seed)
    cv = Canvas(512, 512)
    origin = np.array([cv.w / 2, cv.h / 2]) + rng.uniform(-12, 12, 2)
    n = 0

    def colour():
        if rng.random() < yellow:
            return lin(YELLOW_SRGB / 255.0) * rng.uniform(0.85, 1.1)
        return lin(NEEDLE_SRGB / 255.0) * rng.uniform(0.85, 1.1)

    for layer, (count, reach, width) in enumerate(((11, (0.72, 0.9), (0.32, 0.4)), (8, (0.45, 0.62), (0.34, 0.42)))):
        headings = (np.linspace(0, 2 * math.pi, count, endpoint=False) + rng.uniform(0, 6.3)
                    + rng.uniform(-0.15, 0.15, count))
        for h in headings:
            length = rng.uniform(*reach) * (cv.w / 2 - 30)
            start = origin + unit(h) * rng.uniform(0, 24)
            n += draw_frond(cv, start, h, length, length * rng.uniform(*width), rng, colour(), buds=0.1,
                            needle_len=(22, 32), spacing=4.2)
    for k in range(int(rng.integers(5, 8))):                # short sprays over the hub (no hole at the centre)
        h = rng.uniform(0, 6.3)
        n += draw_frond(cv, origin + rng.uniform(-36, 36, 2), h, rng.uniform(150, 230), 60, rng, colour(),
                        buds=0.0, needle_len=(22, 32), spacing=4.2)
    c, a, nm = cv.result()
    return c, a, nm, n


def make_needles():
    W, Hh = 2048, 2048
    base = np.zeros((Hh, W, 4), np.float32); nrm = np.zeros((Hh, W, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
    cells = []
    jobs = [('frond', 8801 + k, (0, 512 * k, 1024, 512)) for k in range(4)]
    jobs += [('cluster', 8901 + k, (1024, 512 * k, 512, 512)) for k in range(4)]
    jobs += [('cluster_yellow', 8951 + k, (1536, 512 * k, 512, 512)) for k in range(4)]
    for kind, seed, (y0, x0, h, w) in jobs:
        if kind == 'frond':
            c, a, nm, n = frond_cell(seed)
        else:
            c, a, nm, n = cluster_cell(seed, 0.45 if kind == 'cluster_yellow' else 0.0)
        base[y0:y0 + h, x0:x0 + w, :3] = c; base[y0:y0 + h, x0:x0 + w, 3] = a; nrm[y0:y0 + h, x0:x0 + w] = nm
        inside = a > 0.5
        mean = lin(np.clip(c, 0, 1))[inside].mean(0)
        cells.append({'kind': kind, 'uv': [x0 / W, 1 - (y0 + h) / Hh, w / W, h / Hh],
                      'mean_linear': mean.round(5).tolist(), 'coverage': round(float(inside.mean()), 4),
                      'needles': int(n)})
        print('NEEDLES cell', len(cells) - 1, kind, 'needles', n, 'coverage', cells[-1]['coverage'],
              'mean sRGB', (srgb(mean) * 255).round(0))
    inside = base[..., 3] > 0.5
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    base[..., :3] = base[..., :3][idx[0], idx[1]]
    nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'needles_basecolor.png'))
    Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'needles_normal.png'))
    preview = Image.new('RGBA', (W, Hh), (150, 160, 175, 255))
    preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
    preview.convert('RGB').resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, 'needles_preview.png'))
    json.dump({'size': [W, Hh], 'cells': cells}, open(os.path.join(OUT, 'needles.json'), 'w'), indent=1)


def make_bark2():
    """bark2_*: Poly Haven bark_willow_02 (CC0), fibrous ridged bark for the sculpted desert/gorge trees: diffuse x
    AO^2 x height, local contrast raised (CONTRAST2 about the mean luminance) so ridges and crevices read like the
    sprites' high-contrast trunks, graded to a warm light neutral (BARK2_SRGB); species colour from COLOR_0."""
    S = os.path.join(common.SOURCE, 'bark_willow_02')

    def load(name, channels):
        raw = np.asarray(Image.open(os.path.join(S, f'bark_willow_02_{name}_2k.png')))
        values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
        if values.ndim == 3:
            return values[..., :3] if channels == 3 else values[..., :3].mean(2)
        return values if channels == 1 else np.repeat(values[..., None], 3, 2)

    diffuse = lin(load('diff', 3))
    ao = load('ao', 1)
    height = load('disp', 1)
    height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
    bark = diffuse * (ao ** 2.0 * (0.55 + 0.45 * height))[..., None]
    lum = np.maximum(bark @ np.array([0.2126, 0.7152, 0.0722]), 1e-4)
    bark = bark * ((lum / lum.mean()) ** (CONTRAST2 - 1.0))[..., None]
    bark = bark / bark.reshape(-1, 3).mean(0) * lin(np.array(BARK2_SRGB) / 255.0)
    size = (1024, 1024)
    img = Image.fromarray((np.clip(srgb(bark), 0, 1) * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    img.save(os.path.join(OUT, 'bark2_basecolor.png'))
    Image.open(os.path.join(S, 'bark_willow_02_nor_gl_2k.png')).convert('RGB').resize(size, Image.LANCZOS).save(
        os.path.join(OUT, 'bark2_normal.png'))
    rough = (load('rough', 1) * 255).astype(np.uint8); zero = np.zeros_like(rough)
    Image.fromarray(np.stack([zero, rough, zero], 2)).resize(size, Image.LANCZOS).save(os.path.join(OUT, 'bark2_mr.png'))
    mean = lin(np.asarray(img, np.float32) / 255).reshape(-1, 3).mean(0)
    json.dump({'mean_linear': mean.round(5).tolist(), 'srgb': BARK2_SRGB}, open(os.path.join(OUT, 'bark2.json'), 'w'))
    print('BARK2 mean linear', mean.round(4))


BARK2_SRGB = [214, 194, 172]
CONTRAST2 = 2.1

if 'bark' in parts:
    make_bark()
if 'bark2' in parts:
    make_bark2()
if 'needles' in parts:
    make_needles()
