#!/usr/bin/env python3
"""Procedural textures for the MM6 succulents (cacti, desert shrub, dry weeds), painted with numpy/PIL at
supersampling; no external images. Colours are sRGB values taken from the native sprites. Each texture writes
textures/<name>_basecolor.png (RGB, or RGBA for cut-out cards) and <name>_normal.png (OpenGL tangent space, from a
painted height field). Tiles wrap in u and v (rib skins, rock); atlases are 2 x 2 cells and have their colour dilated
into transparent texels so mips never pick up a halo. Every texture has its own seed: adding one never changes the
others. Usage: make_textures.py [name ...] (default: all)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures')
os.makedirs(OUT, exist_ok=True)


class Canvas:
    """Supersampled paint surface in normalised coordinates (x right, y down, 0..1 over the whole image)."""

    def __init__(self, width, height, ss, wrap, seed):
        self.w, self.h, self.ss, self.wrap = width, height, ss, wrap
        self.W, self.H = width * ss, height * ss
        self.col = np.zeros((self.H, self.W, 3), np.float32)
        self.a = np.zeros((self.H, self.W), np.float32)
        self.hgt = np.zeros((self.H, self.W), np.float32)
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------ fields
    def noise(self, beta=2.0, scale=(1.0, 1.0), size=None):
        """Periodic fractal noise in [0, 1] at canvas resolution (or `size` = (h, w))."""
        h, w = size or (self.H, self.W)
        field = self.rng.normal(size=(h, w))
        fy = np.fft.fftfreq(h)[:, None] * scale[1]; fx = np.fft.fftfreq(w)[None, :] * scale[0]
        r = np.sqrt(fx * fx + fy * fy); r[0, 0] = 1.0
        spec = np.fft.fft2(field) / r ** beta; spec[0, 0] = 0
        v = np.real(np.fft.ifft2(spec))
        return ((v - v.min()) / (v.max() - v.min())).astype(np.float32)

    def grid(self):
        y, x = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        return (x + 0.5) / self.W, (y + 0.5) / self.H

    def fill(self, rgb, height=0.0):
        self.col[:] = np.asarray(rgb, np.float32); self.a[:] = 1.0; self.hgt[:] = height

    # ------------------------------------------------------------ stamping
    def poly(self, pts, rgb, height=None, opacity=1.0, alpha=True, hmode='set'):
        """Fill polygon `pts` (normalised) with a colour (rgb or callable(x, y) -> (h, w, 3) on the local box)."""
        P = [(x * self.W, y * self.H) for x, y in pts]
        xs = [p[0] for p in P]; ys = [p[1] for p in P]
        shifts = [(0, 0)]
        if self.wrap:
            for dx in (-self.W, 0, self.W):
                for dy in (-self.H, 0, self.H):
                    if (dx, dy) != (0, 0) and min(xs) + dx < self.W and max(xs) + dx > 0 \
                            and min(ys) + dy < self.H and max(ys) + dy > 0:
                        shifts.append((dx, dy))
        for dx, dy in shifts:
            x0, x1 = int(max(min(xs) + dx - 1, 0)), int(min(max(xs) + dx + 2, self.W))
            y0, y1 = int(max(min(ys) + dy - 1, 0)), int(min(max(ys) + dy + 2, self.H))
            if x1 <= x0 or y1 <= y0:
                continue
            im = Image.new('L', (x1 - x0, y1 - y0), 0)
            ImageDraw.Draw(im).polygon([(x + dx - x0, y + dy - y0) for x, y in P], fill=255)
            m = np.asarray(im, np.float32) / 255.0 * opacity
            if m.max() <= 0:
                continue
            reg = (slice(y0, y1), slice(x0, x1))
            if callable(rgb):
                yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
                c = rgb((xx - dx + 0.5) / self.W, (yy - dy + 0.5) / self.H)
            else:
                c = np.asarray(rgb, np.float32)[None, None]
            self.col[reg] = self.col[reg] * (1 - m[..., None]) + c * m[..., None]
            if alpha:
                self.a[reg] = np.maximum(self.a[reg], m)
            if height is not None:
                if hmode == 'max':
                    self.hgt[reg] = np.maximum(self.hgt[reg], height * m + self.hgt[reg] * (1 - m))
                elif hmode == 'add':
                    self.hgt[reg] += height * m
                else:
                    self.hgt[reg] = self.hgt[reg] * (1 - m) + height * m

    def ellipse(self, cx, cy, rx, ry, rgb, height=None, opacity=1.0, n=16, angle=0.0, hmode='set', alpha=True):
        ca, sa = math.cos(angle), math.sin(angle)
        pts = []
        for k in range(n):
            t = 2 * math.pi * k / n
            x, y = math.cos(t) * rx, math.sin(t) * ry
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.poly(pts, rgb, height, opacity, hmode=hmode, alpha=alpha)

    def stroke(self, pts, w0, w1, c0, c1, h0=None, h1=None, aspect=1.0, opacity=1.0, hmode='max'):
        """Tapered polyline (normalised points), width w0 -> w1 (in x units; y widths scaled by aspect = W/H),
        colour c0 -> c1 along it, one polygon per segment."""
        n = len(pts) - 1
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            dx, dy = (xb - xa), (yb - ya) * (self.H / self.W)
            L = math.hypot(dx, dy) or 1e-9
            nx, ny = -dy / L, dx / L
            ta, tb = i / n, (i + 1) / n
            wa = (w0 + (w1 - w0) * ta) * 0.5; wb = (w0 + (w1 - w0) * tb) * 0.5
            ny_n = ny * (self.W / self.H)
            quad = [(xa + nx * wa, ya + ny_n * wa), (xb + nx * wb, yb + ny_n * wb),
                    (xb - nx * wb, yb - ny_n * wb), (xa - nx * wa, ya - ny_n * wa)]
            t = (ta + tb) / 2
            c = [c0[k] + (c1[k] - c0[k]) * t for k in range(3)]
            h = None if h0 is None else h0 + (h1 - h0) * t
            self.poly(quad, c, h, opacity, hmode=hmode)

    def jitter(self, rgb, amount):
        f = 1 + self.rng.uniform(-amount, amount)
        return [min(max(c * f, 0.0), 1.0) for c in rgb]

    # ------------------------------------------------------------ output
    def save(self, name, strength=4.0, cutout=False, blur=0.7):
        ss = self.ss

        def down(x):
            return x.reshape(self.h, ss, self.w, ss).mean((1, 3))
        a = down(self.a)
        if cutout:
            rgb = np.stack([down(self.col[..., c] * self.a) for c in range(3)], -1) / np.maximum(a, 1e-4)[..., None]
            hg = down(self.hgt * self.a)
        else:
            rgb = np.stack([down(self.col[..., c]) for c in range(3)], -1); hg = down(self.hgt)
        mode = 'wrap' if self.wrap else 'nearest'
        hg = ndimage.gaussian_filter(hg, blur, mode=mode)
        if self.wrap:
            gx = (np.roll(hg, -1, 1) - np.roll(hg, 1, 1)) * 0.5; gy = (np.roll(hg, -1, 0) - np.roll(hg, 1, 0)) * 0.5
        else:
            gy, gx = np.gradient(hg)
        n = np.stack([-gx * strength, gy * strength, np.ones_like(hg)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        if cutout:
            covered = a > 0.02
            _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
            rgb = rgb[iy, ix]; n = n[iy, ix]
        rgb8 = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
        if cutout:
            Image.fromarray(np.dstack([rgb8, (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)]), 'RGBA').save(
                os.path.join(OUT, f'{name}_basecolor.png'))
        else:
            Image.fromarray(rgb8, 'RGB').save(os.path.join(OUT, f'{name}_basecolor.png'))
        Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(
            os.path.join(OUT, f'{name}_normal.png'))
        mean = rgb[a > 0.5].mean(0) * 255 if (a > 0.5).any() else np.zeros(3)
        print('TEXTURE', name, f'{self.w}x{self.h}', 'coverage', round(float((a > 0.5).mean()), 3),
              'mean', mean.round().tolist())


def mix(a, b, t):
    t = np.asarray(t, np.float32)[..., None]
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


# =================================================================== rib skins (u = one rib, valley at 0 and 1)
def rib_base(cv, valley, flank, crest, crest_width=0.18, streaks=0.10, mottle=0.12, mottle_rgb=None,
             mottle_beta=2.0):
    x, y = cv.grid()
    d = np.abs(x - 0.5) * 2                                 # 0 crest .. 1 valley
    t_valley = np.clip((d - 0.55) / 0.45, 0, 1) ** 1.4
    t_crest = np.clip(1 - d / crest_width, 0, 1)
    col = mix(flank, valley, t_valley)
    col = mix(col, crest, t_crest)
    s = cv.noise(1.4, (0.35, 6.0))                          # vertical streaks (smooth along v)
    m = cv.noise(mottle_beta, (1.0, 1.0))
    col *= (1 + (s - 0.5) * 2 * streaks)[..., None]
    if mottle_rgb is not None:
        col = mix(col, mottle_rgb, np.clip((m - 0.55) * 3.0, 0, 1) * mottle * 4)
    else:
        col *= (1 + (m - 0.5) * 2 * mottle)[..., None]
    cv.col[:] = col; cv.a[:] = 1
    cv.hgt[:] = (1 - d) * 0.25 + (s - 0.5) * 0.05 + (m - 0.5) * 0.08


def radial_spines(cv, cx, cy, count, length, width, c_base, c_tip, spread=(0, 2 * math.pi), curve=0.25, h=1.0,
                  rot=None, lmin=0.55):
    rot = cv.rng.uniform(0, 2 * math.pi) if rot is None else rot
    aspect = cv.w / cv.h
    for k in range(count):
        a = rot + spread[0] + (spread[1] - spread[0]) * (k + cv.rng.uniform(0.2, 0.8)) / count
        L = length * cv.rng.uniform(lmin, 1.0)
        bend = cv.rng.normal(0, curve)
        pts = []
        px, py = cx, cy
        for s in range(6):
            pts.append((px, py))
            aa = a + bend * s / 5
            px += math.cos(aa) * L / 5; py += math.sin(aa) * L / 5 * aspect
        cv.stroke(pts, width, width * 0.15, cv.jitter(c_base, 0.08), cv.jitter(c_tip, 0.05), h * 0.8, h)


def tex_barrel_skin():
    """cac8 golden barrel: one rib 256 x 1024 (0.31 x 1.0 m), dark green flanks, six woolly areoles on the crest, long
    pale yellow spines radiating over the neighbouring ribs (they cover most of the body, as in the sprite)."""
    cv = Canvas(256, 1024, 3, True, 801)
    rib_base(cv, (0.10, 0.14, 0.05), (0.24, 0.31, 0.10), (0.42, 0.44, 0.16), crest_width=0.25, streaks=0.08)
    rows = [(k + 0.5) / 6 + cv.rng.normal(0, 0.01) for k in range(6)]
    for v in rows:
        cv.ellipse(0.5, v, 0.08, 0.016, (0.80, 0.70, 0.36), 0.55, n=12)
    for v in rows:
        # radial spines: long, curving, crossing into the neighbour ribs; three stout centrals
        radial_spines(cv, 0.5, v, 13, 1.05, 0.05, (0.66, 0.56, 0.22), (0.98, 0.93, 0.66), curve=0.35, h=1.0, lmin=0.4)
        radial_spines(cv, 0.5, v, 4, 0.40, 0.046, (0.70, 0.58, 0.22), (0.99, 0.94, 0.66), spread=(-2.4, -0.7),
                      rot=0.0, curve=0.1, h=1.2)
        radial_spines(cv, 0.5, v, 3, 0.40, 0.046, (0.70, 0.58, 0.22), (0.99, 0.94, 0.66), spread=(0.7, 2.4),
                      rot=0.0, curve=0.1, h=1.2)
    cv.save('barrel_skin', strength=5.0)


def tex_barrel_spines():
    """Cut-out spine layer over the barrel (a shell above the body and fringe cards on the crests), tiling like
    barrel_skin (256 x 1024 = one rib x 1 m): stout cream-yellow spines radiating from the six crest areoles."""
    cv = Canvas(256, 1024, 3, True, 802)
    cv.a[:] = 0
    rows = [(k + 0.5) / 6 for k in range(6)]
    for v in rows:
        radial_spines(cv, 0.5, v, 10, 1.25, 0.06, (0.70, 0.60, 0.26), (0.99, 0.95, 0.70), curve=0.4, h=1.0, lmin=0.4)
        radial_spines(cv, 0.5, v, 4, 0.45, 0.065, (0.78, 0.66, 0.30), (1.0, 0.96, 0.72), spread=(-2.5, -0.6),
                      rot=0.0, curve=0.1, h=1.2)
    cv.save('barrel_spines', strength=3.0, cutout=True)


def tex_organ_skin():
    """cac5 candelabra columns: one deep wing-rib 256 x 512 (0.34 x 0.34 m): bright green flanks with streaks, the
    crest a pale yellow-green toothed margin (one tooth per areole, five per tile) with brown spine pairs."""
    cv = Canvas(256, 512, 3, True, 805)
    rib_base(cv, (0.07, 0.23, 0.10), (0.27, 0.56, 0.30), (0.48, 0.72, 0.40), crest_width=0.35, streaks=0.14)
    period = 1 / 5
    for k in range(6):
        v = k * period
        # dark notch shading below each tooth, then the pale tooth (a chevron pointing up the stem)
        cv.poly([(0.5, v - 0.02), (0.64, v + 0.06), (0.5, v + 0.13), (0.36, v + 0.06)], (0.04, 0.16, 0.06), 0.1)
        cv.poly([(0.5, v - 0.075), (0.60, v - 0.02), (0.57, v + 0.035), (0.5, v + 0.06), (0.43, v + 0.035),
                 (0.40, v - 0.02)], lambda X, Y: mix((0.86, 0.90, 0.58), (0.55, 0.72, 0.36),
                                                    np.clip((Y - (v - 0.075)) / 0.135, 0, 1)), 0.5)
        cv.ellipse(0.5, v - 0.055, 0.022, 0.009, (0.90, 0.88, 0.70), 0.7, n=10)
        for side in (-1, 1):
            a = -math.pi / 2 + side * 0.9 + cv.rng.normal(0, 0.15)
            cv.stroke([(0.5, v - 0.055), (0.5 + math.cos(a) * 0.08, v - 0.055 + math.sin(a) * 0.04)], 0.02, 0.004,
                      (0.50, 0.36, 0.20), (0.22, 0.15, 0.10), 0.8, 0.9)
    cv.save('organ_skin', strength=4.0)


def tex_saguaro_skin():
    """cac16 column: one rounded rib 256 x 512 (0.13 x 0.26 m): mottled green with paler waxy patches, low tubercle
    bumps round two felted cream areoles per tile (offset half a tile on alternate ribs by the build's per-rib
    offsets), short white and brown spines."""
    cv = Canvas(256, 512, 3, True, 816)
    rib_base(cv, (0.24, 0.38, 0.20), (0.36, 0.52, 0.29), (0.47, 0.62, 0.38), crest_width=0.5, streaks=0.08,
             mottle=0.16, mottle_rgb=(0.60, 0.66, 0.52), mottle_beta=1.2)
    spots = cv.noise(1.0, (3.0, 1.5))
    cv.col[:] = mix(cv.col, (0.66, 0.68, 0.56), np.clip((spots - 0.70) * 6, 0, 1) * 0.6)
    x, y = cv.grid()
    rows = (0.11, 0.36, 0.61, 0.86)
    bump = np.zeros_like(x)
    for v in rows:
        for dv in (-1, 0, 1):
            d = np.sqrt(((x - 0.5) / 0.45) ** 2 + ((y - v - dv) / 0.12) ** 2)
            bump = np.maximum(bump, np.clip(1 - d, 0, 1) ** 1.5)
    cv.hgt[:] += bump * 0.5
    cv.col[:] *= (0.92 + 0.14 * bump)[..., None]
    for v in rows:
        cv.ellipse(0.5, v - 0.01, 0.30, 0.055, (0.40, 0.36, 0.30), 0.7, n=16)
        cv.ellipse(0.5, v - 0.01, 0.22, 0.040, (0.93, 0.91, 0.84), 0.9, n=14)
        cv.ellipse(0.5, v - 0.01, 0.08, 0.014, (0.45, 0.38, 0.30), 0.9, n=10)
        radial_spines(cv, 0.5, v - 0.01, 10, 0.55, 0.04, (0.62, 0.52, 0.38), (0.97, 0.95, 0.90), curve=0.1, h=1.0,
                      lmin=0.45)
        radial_spines(cv, 0.5, v - 0.01, 2, 0.26, 0.04, (0.40, 0.30, 0.20), (0.70, 0.60, 0.46), spread=(-2.0, -1.1),
                      rot=0.0, curve=0.05, h=1.1)
    cv.save('saguaro_skin', strength=5.0)


# =================================================================== prickly-pear pad atlases (1024, cells of 512)
def cell_xy(cell, x, y):
    return ((cell % 2) + x) * 0.5, ((cell // 2) + y) * 0.5


def pad(cv, cell, rx, ry, base, rim, centre, areole, glochid, spine=None, spine_len=0.0, spacing=0.085,
        mottle=0.15, obovate=0.12, blotch=None, gain=1.0, rim_light=None, halo=None):
    """One pad in a cell: an obovate oval (cell-local semi-axes rx, ry round (0.5, 0.52)) with a darker rim, lighter
    centre, mottling, a quincunx grid of areoles (dot + glochid tuft) and optional long spines, some reaching past
    the outline into the transparent margin."""
    cx, cy = 0.5, 0.52

    def inside_radius(x, y):
        dy = (y - cy) / ry
        wx = rx * (1 + obovate * np.clip(-dy, -1, 1))
        return np.sqrt(((x - cx) / wx) ** 2 + dy ** 2)
    mott = cv.noise(2.0, (1.0, 1.0))
    speck = cv.noise(0.6, (1.0, 1.0))

    def colour(X, Y):
        lx, ly = (X * 2) % 1, (Y * 2) % 1
        r = inside_radius(lx, ly)
        c = mix(centre, base, np.clip(r * 1.15, 0, 1))
        c = mix(c, rim, np.clip((r - 0.80) / 0.2, 0, 1))
        iy = np.clip((Y * cv.H).astype(int), 0, cv.H - 1); ix = np.clip((X * cv.W).astype(int), 0, cv.W - 1)
        n = mott[iy, ix]
        c = c * (1 + (n - 0.5) * 2 * mottle + (speck[iy, ix] - 0.5) * 0.35)[..., None]
        if blotch is not None:
            c = mix(c, blotch[0], np.clip((n - blotch[1]) * 5, 0, 1) * 0.8)
        if rim_light is not None:                      # thin pale margin, as the sprites' lit pad edges
            c = mix(c, rim_light, np.clip((r - 0.90) / 0.08, 0, 1) * 0.7)
        return np.clip(c * gain, 0, 1)
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        dy = math.sin(t)
        wx = rx * (1 + obovate * max(min(-dy, 1), -1))
        pts.append(cell_xy(cell, cx + math.cos(t) * wx, cy + dy * ry))
    # height: a dome over the pad
    x0, y0 = cell_xy(cell, 0, 0)
    sl = (slice(int(y0 * cv.H), int((y0 + 0.5) * cv.H)), slice(int(x0 * cv.W), int((x0 + 0.5) * cv.W)))
    before = cv.a[sl].copy()
    cv.poly(pts, colour, None)
    yy, xx = np.mgrid[0:cv.H // 2, 0:cv.W // 2].astype(np.float32)
    r = inside_radius((xx + 0.5) / (cv.W / 2), (yy + 0.5) / (cv.H / 2))
    cv.hgt[sl] = np.where(cv.a[sl] > before, np.sqrt(np.clip(1 - r ** 2, 0, 1)) * 0.8, cv.hgt[sl])
    # areoles in diagonal rows
    rows = int(2 * ry / spacing) + 2
    for i in range(-rows, rows + 1):
        for j in range(-rows, rows + 1):
            ax = cx + (j + 0.5 * (i % 2)) * spacing * 1.05 + cv.rng.normal(0, 0.006)
            ay = cy + i * spacing * 0.9 + cv.rng.normal(0, 0.006)
            rr = float(inside_radius(np.float32(ax), np.float32(ay)))
            if rr > 0.93:
                continue
            gx, gy = cell_xy(cell, ax, ay)
            if halo is not None:
                cv.ellipse(gx, gy, 0.010, 0.010, cv.jitter(halo, 0.06), 0.9, n=10, hmode='add')
            cv.ellipse(gx, gy, 0.0055, 0.0055, cv.jitter(areole, 0.1), 0.95, n=8, hmode='add')
            cv.ellipse(gx, gy - 0.001, 0.003, 0.003, cv.jitter(glochid, 0.08), 1.05, n=6, hmode='add')
            if spine is not None and cv.rng.uniform() < 0.55:
                outward = math.atan2(ay - cy, ax - cx) if rr > 0.25 else cv.rng.uniform(0, 2 * math.pi)
                for s in range(int(cv.rng.integers(1, 3))):
                    a = outward + cv.rng.normal(0, 0.6)
                    L = spine_len * cv.rng.uniform(0.5, 1.0) * (1.4 if rr > 0.75 else 1.0)
                    cv.stroke([(gx, gy), (gx + math.cos(a) * L * 0.5, gy + math.sin(a) * L * 0.5)],
                              0.0028, 0.0006, spine, (min(spine[0] * 1.1, 1), min(spine[1] * 1.1, 1),
                                                       min(spine[2] * 1.1, 1)), 1.1, 1.2)


def fruit_cell(cv, cell, fruit_a, fruit_b, stem, flower=None):
    """Cell 3: fruit swatches (top half: left fruit_a, right fruit_b, areole dots), lower half a woody stem/dry pad
    strip; optional flower (petal ring) in the lower right quarter."""
    x0, y0 = cell_xy(cell, 0, 0)
    for (fx, rgb) in ((0.0, fruit_a), (0.25, fruit_b)):
        def fc(X, Y, rgb=rgb):
            n = cv.noise(2.0, (1, 1), size=X.shape)
            return np.asarray(rgb, np.float32)[None, None] * (0.85 + 0.3 * n)[..., None]
        cv.poly([(x0 + fx, y0), (x0 + fx + 0.25, y0), (x0 + fx + 0.25, y0 + 0.25), (x0 + fx, y0 + 0.25)], fc, 0.5)
        for k in range(14):
            cv.ellipse(x0 + fx + cv.rng.uniform(0.02, 0.23), y0 + cv.rng.uniform(0.02, 0.23), 0.004, 0.004,
                       (0.75, 0.68, 0.40), 0.8, n=6)
    def sc(X, Y):
        n = cv.noise(1.6, (1, 3), size=X.shape)
        return np.asarray(stem, np.float32)[None, None] * (0.7 + 0.5 * n)[..., None]
    cv.poly([(x0, y0 + 0.25), (x0 + 0.25, y0 + 0.25), (x0 + 0.25, y0 + 0.5), (x0, y0 + 0.5)], sc, 0.4)
    if flower is not None:
        fx, fy = x0 + 0.375, y0 + 0.375
        for k in range(10):
            a = 2 * math.pi * k / 10 + cv.rng.normal(0, 0.1)
            cv.ellipse(fx + math.cos(a) * 0.05, fy + math.sin(a) * 0.05, 0.05, 0.03, cv.jitter(flower, 0.06), 0.6,
                       n=12, angle=a)
        cv.ellipse(fx, fy, 0.03, 0.03, (0.85, 0.80, 0.35), 0.8, n=12)


def tex_pads_cac7():
    """cac7: long upright blue-green pads, densely dotted with pale areoles, few spines."""
    cv = Canvas(1024, 1024, 2, False, 807)
    common = dict(spacing=0.07, obovate=0.10, gain=1.25, rim_light=(0.62, 0.62, 0.30))
    pad(cv, 0, 0.21, 0.45, (0.20, 0.36, 0.18), (0.12, 0.24, 0.10), (0.30, 0.46, 0.22), (0.62, 0.62, 0.45),
        (0.85, 0.82, 0.62), **common)
    pad(cv, 1, 0.22, 0.45, (0.15, 0.29, 0.15), (0.09, 0.19, 0.09), (0.24, 0.40, 0.20), (0.55, 0.56, 0.42),
        (0.80, 0.78, 0.60), **common)
    pad(cv, 2, 0.24, 0.42, (0.30, 0.45, 0.22), (0.18, 0.30, 0.12), (0.40, 0.55, 0.28), (0.66, 0.64, 0.46),
        (0.88, 0.85, 0.66), **common)
    fruit_cell(cv, 3, (0.30, 0.42, 0.20), (0.45, 0.30, 0.20), (0.28, 0.30, 0.18))
    cv.save('pads_cac7', strength=3.0, cutout=True)


def tex_pads_cac10():
    """cac10: round bright green pads with brown areoles and white spines; brown-red fruit."""
    cv = Canvas(1024, 1024, 2, False, 810)
    sp = dict(spine=(0.86, 0.84, 0.74), spine_len=0.07, spacing=0.10, gain=1.15, rim_light=(0.55, 0.70, 0.40),
              halo=(0.55, 0.68, 0.40))
    pad(cv, 0, 0.36, 0.44, (0.30, 0.58, 0.30), (0.17, 0.38, 0.18), (0.40, 0.66, 0.36), (0.42, 0.30, 0.18),
        (0.80, 0.72, 0.45), **sp)
    pad(cv, 1, 0.37, 0.43, (0.22, 0.47, 0.24), (0.12, 0.30, 0.14), (0.32, 0.56, 0.30), (0.38, 0.27, 0.16),
        (0.76, 0.68, 0.42), **sp)
    pad(cv, 2, 0.34, 0.44, (0.40, 0.64, 0.34), (0.24, 0.44, 0.22), (0.50, 0.72, 0.42), (0.46, 0.34, 0.20),
        (0.82, 0.75, 0.50), **sp)
    fruit_cell(cv, 3, (0.48, 0.30, 0.18), (0.40, 0.42, 0.20), (0.36, 0.30, 0.22))
    cv.save('pads_cac10', strength=3.0, cutout=True)


def tex_pads_cac15():
    """cac15: olive pads with long white spines (past the outline), a corky purple-brown old pad, pink fruit."""
    cv = Canvas(1024, 1024, 2, False, 815)
    sp = dict(spine=(0.90, 0.88, 0.82), spine_len=0.10, spacing=0.10, gain=1.3, rim_light=(0.55, 0.58, 0.36))
    pad(cv, 0, 0.34, 0.43, (0.34, 0.40, 0.23), (0.21, 0.27, 0.15), (0.43, 0.48, 0.29), (0.40, 0.32, 0.22),
        (0.82, 0.78, 0.62), **sp)
    pad(cv, 1, 0.33, 0.43, (0.19, 0.29, 0.15), (0.11, 0.19, 0.10), (0.28, 0.38, 0.21), (0.36, 0.28, 0.20),
        (0.80, 0.76, 0.60), **sp)
    pad(cv, 2, 0.35, 0.42, (0.40, 0.34, 0.24), (0.23, 0.19, 0.13), (0.47, 0.42, 0.30), (0.30, 0.24, 0.18),
        (0.70, 0.66, 0.58), spine=(0.85, 0.82, 0.75), spine_len=0.06, spacing=0.12, mottle=0.45,
        blotch=((0.60, 0.57, 0.46), 0.58), gain=1.1)
    fruit_cell(cv, 3, (0.78, 0.36, 0.48), (0.55, 0.20, 0.32), (0.36, 0.27, 0.24), flower=(0.92, 0.55, 0.62))
    cv.save('pads_cac15', strength=3.0, cutout=True)


# =================================================================== shrub / weed card atlases
def sprig_fan(cv, cell, stems, stem0, stem1, leaf0, leaf1, leaf_count, leaf_len, leaf_w, spread=1.1, length=(0.55, 0.92),
              branch=2, seeds=None, base_w=0.006, leaf_kind='needle', tip_from=0.35):
    """A fan of thin branching stems from the cell's bottom centre, leaves (needles or seed dots) along the outer
    part of each branch, denser toward the tips."""
    rng = cv.rng

    def grow(x, y, a, L, w, depth):
        bend = rng.normal(0, 0.25)
        x0, y0 = x, y
        for attempt in range(8):                     # shorten until the branch stays inside its cell
            pts = [(x0, y0)]; x, y = x0, y0
            for s in range(6):
                aa = a + bend * s / 5
                x += math.sin(aa) * L / 6; y -= math.cos(aa) * L / 6
                pts.append((x, y))
            if all(0.03 < px < 0.97 and 0.03 < py <= 1.0 for px, py in pts):
                break
            L *= 0.8
        gpts = [cell_xy(cell, px, py) for px, py in pts]
        cv.stroke(gpts, w, w * 0.4, cv.jitter(stem0, 0.08), cv.jitter(stem1, 0.08), 0.3, 0.6)
        if depth < branch:
            for b in range(int(rng.integers(1, 3))):
                k = int(rng.integers(2, 5))
                bx, by = pts[k]
                grow(bx, by, a + bend * k / 5 + rng.choice([-1, 1]) * rng.uniform(0.3, 0.7), L * rng.uniform(0.4, 0.6),
                     w * 0.6, depth + 1)
        n = int(leaf_count * L / length[1])
        for i in range(n):
            t = rng.uniform(tip_from, 1.0) ** 0.6
            k = min(int(t * 6), 5); f = t * 6 - k
            px = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f; py = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f
            lc = mix(leaf0, leaf1, t * rng.uniform(0.6, 1.0)).tolist()
            if leaf_kind == 'needle':
                la = a + rng.choice([-1, 1]) * rng.uniform(0.3, 1.0)
                ll = leaf_len * rng.uniform(0.6, 1.0)
                gx0, gy0 = cell_xy(cell, px, py)
                gx1, gy1 = cell_xy(cell, px + math.sin(la) * ll, py - math.cos(la) * ll)
                cv.stroke([(gx0, gy0), ((gx0 + gx1) / 2, (gy0 + gy1) / 2), (gx1, gy1)], leaf_w, leaf_w * 0.3,
                          cv.jitter(lc, 0.06), cv.jitter([min(c * 1.15, 1) for c in lc], 0.06), 0.6, 0.9)
            else:
                gx0, gy0 = cell_xy(cell, px + rng.normal(0, leaf_len * 0.3), py + rng.normal(0, leaf_len * 0.3))
                cv.ellipse(gx0, gy0, leaf_w, leaf_w * rng.uniform(0.7, 1.3), cv.jitter(lc, 0.1), 0.8, n=7,
                           angle=rng.uniform(0, math.pi))
    for k in range(stems):
        side = rng.uniform(-1, 1)
        grow(0.5 + side * 0.10, 0.995, side * spread + rng.normal(0, 0.1), rng.uniform(*length) * (1 - 0.2 * abs(side)),
             base_w, 0)


def sage_puff(cv, cell, light, needles=1100):
    """One rounded sage puff: dark lilac-grey stems fanning from the bottom centre, then fine needle leaves packed in
    a dome, dark low and inside, silvery blue-white toward the rim and top (drawn dark to light)."""
    rng = cv.rng
    for k in range(16):
        a = rng.uniform(-0.8, 0.8); L = rng.uniform(0.40, 0.62)
        x0 = 0.5 + rng.normal(0, 0.04)
        pts = [cell_xy(cell, x0 + math.sin(a) * L * t * (0.6 + 0.4 * t), 0.995 - math.cos(a) * L * t) for t in np.linspace(0, 1, 6)]
        cv.stroke(pts, 0.008, 0.003, (0.16 * light, 0.17 * light, 0.24 * light), (0.34 * light, 0.36 * light, 0.46 * light), 0.3, 0.6)
    leaves = []
    for k in range(needles):
        while True:
            x, y = rng.uniform(0.04, 0.96), rng.uniform(0.04, 0.92)
            r = math.hypot((x - 0.5) / 0.45, (y - 0.50) / 0.44)
            if r < 1.0:
                break
        bright = min(1.0, max(0.0, 0.25 + 0.75 * r ** 1.4 * (1.15 - 0.5 * y) + rng.normal(0, 0.12)))
        leaves.append((bright, x, y))
    for bright, x, y in sorted(leaves):
        a = math.atan2(x - 0.5, 1.0 - y) + rng.normal(0, 0.5)
        L = rng.uniform(0.028, 0.05)
        c = mix((0.22, 0.25, 0.34), (0.86, 0.91, 0.97), bright ** 0.8).tolist()
        c = [v * light for v in c]
        x1, y1 = x + math.sin(a) * L, y - math.cos(a) * L
        cv.stroke([cell_xy(cell, x, y), cell_xy(cell, (x + x1) / 2, (y + y1) / 2), cell_xy(cell, x1, y1)], 0.006, 0.002,
                  [v * 0.8 for v in c], c, 0.5 + 0.5 * bright, 0.6 + 0.5 * bright)


def tex_sage_cac27():
    """cac27: silvery-blue desert sage. Cells 0/1 rounded puffs (dark stems, needle leaves silvery toward the rim),
    cell 2 a darker interior puff, cell 3 the grey-brown dead branch strip (u 0-0.25)."""
    cv = Canvas(1024, 1024, 2, False, 827)
    for cell, light in ((0, 1.0), (1, 0.93), (2, 0.6)):
        sage_puff(cv, cell, light)
    x0, y0 = cell_xy(3, 0, 0)

    def wood(X, Y):
        n = cv.noise(1.2, (0.4, 8.0), size=X.shape)
        return mix((0.30, 0.25, 0.22), (0.62, 0.56, 0.52), n)
    cv.poly([(x0, y0), (x0 + 0.125, y0), (x0 + 0.125, y0 + 0.5), (x0, y0 + 0.5)], wood, 0.5)
    cv.save('sage_cac27', strength=3.0, cutout=True)


def tex_rock_cac27():
    """cac27 rock base: tileable 512 (about 0.7 m) weathered grey-tan stone: mottled base, a network of dark cracks
    (ridged noise) with pale weathered lips, faint horizontal bedding and dark lichen specks."""
    cv = Canvas(512, 512, 2, True, 828)
    n1 = cv.noise(2.0, (1, 1)); n2 = cv.noise(1.7, (1, 1)); n3 = cv.noise(0.9, (1, 1)); n4 = cv.noise(1.8, (0.5, 2.5))
    col = mix((0.22, 0.22, 0.20), (0.60, 0.58, 0.52), np.clip(n1 * 1.4 - 0.2, 0, 1))
    col = mix(col, (0.50, 0.45, 0.37), np.clip((n4 - 0.55) * 2, 0, 1) * 0.35)            # tan bedding
    ridge = np.abs(n2 - 0.5)
    crack = np.clip(1 - ridge / 0.035, 0, 1)
    lip = np.clip(1 - np.abs(ridge - 0.07) / 0.03, 0, 1)
    col = mix(col, (0.80, 0.77, 0.70), lip * 0.35)
    col = mix(col, (0.10, 0.09, 0.08), crack * 0.9)
    col = mix(col, (0.16, 0.16, 0.13), np.clip((n3 - 0.80) * 8, 0, 1) * 0.6)            # lichen specks
    cv.col[:] = col; cv.a[:] = 1
    cv.hgt[:] = n1 * 0.6 - crack * 0.6 + lip * 0.1 + n3 * 0.15
    cv.save('rock_cac27', strength=6.0)


def tex_weeds_snoweed1():
    """snoweed1: dry russet weeds. Cells 0-2 fans of thin orange-brown stems branching into seed clusters at the
    tips (cell 2 shorter and darker), cell 3 a low tuft of fine dry grass blades."""
    cv = Canvas(1024, 1024, 2, False, 901)
    for cell, (light, length) in enumerate(((1.0, (0.6, 0.95)), (0.9, (0.55, 0.9)), (0.7, (0.35, 0.6)))):
        sprig_fan(cv, cell, 16, (0.34 * light, 0.28 * light, 0.24 * light), (0.70 * light, 0.56 * light, 0.43 * light),
                  (0.50 * light, 0.32 * light, 0.20 * light), (0.88 * light, 0.60 * light, 0.38 * light),
                  leaf_count=22, leaf_len=0.02, leaf_w=0.0048, spread=0.6, length=length, branch=3,
                  leaf_kind='seed', base_w=0.0055, tip_from=0.6)
    for k in range(60):
        side = cv.rng.uniform(-1, 1)
        a = side * 0.6 + cv.rng.normal(0, 0.1); L = cv.rng.uniform(0.3, 0.75) * (1 - 0.35 * abs(side))
        x, y = 0.5 + side * 0.15, 0.995
        pts = []
        bend = side * 0.4
        for s in range(6):
            pts.append(cell_xy(3, x, y)); aa = a + bend * s / 5
            x += math.sin(aa) * L / 5; y -= math.cos(aa) * L / 5
        light = cv.rng.uniform(0.7, 1.1)
        cv.stroke(pts, 0.010, 0.002, (0.32 * light, 0.22 * light, 0.15 * light), (0.80 * light, 0.55 * light, 0.32 * light),
                  0.4, 0.7)
    cv.save('weeds_snoweed1', strength=3.0, cutout=True)


TEXTURES = {'barrel_skin': tex_barrel_skin, 'barrel_spines': tex_barrel_spines, 'organ_skin': tex_organ_skin,
            'saguaro_skin': tex_saguaro_skin, 'pads_cac7': tex_pads_cac7, 'pads_cac10': tex_pads_cac10,
            'pads_cac15': tex_pads_cac15, 'sage_cac27': tex_sage_cac27, 'rock_cac27': tex_rock_cac27,
            'weeds_snoweed1': tex_weeds_snoweed1}

if __name__ == '__main__':
    for name in (sys.argv[1:] or TEXTURES):
        TEXTURES[name]()
