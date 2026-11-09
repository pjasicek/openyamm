#!/usr/bin/env python3
"""Textures of the MM8 animated decorations (textures/<name>_{basecolor,normal,mr}.png, mr = glTF
metallic-roughness: G roughness, B metal) and their linear mean colours (textures/means.json; the COLOR_0 tints bring
each material to the native sprite's measured colour, so every set is graded a little brighter than what it serves).

PBR sets derived from CC0 Poly Haven scans (source/polyhaven/, fetch_textures.py), graded as in the MM6 fire batch
(the scan's light/dark structure, chroma reduced and turned to a hue, mean luminance set):

| set | scan | used by |
|---|---|---|
| iron_dark | rusty_metal_04 | lantern dec07, chandelier dec27 iron |
| iron_smooth | blue_metal_plate (scratches) | lantern hood and bowl |
| iron_grey | rusty_metal_02 (rust spots flattened) | chandelier dec08 |
| copper | blue_metal_plate (scratches) | candlestick dec02, buoy dec30 cage and rings |
| brass | blue_metal_plate (scratches) | buoy bell and dome |
| wax | leather_white (grain) | candles |
| wood | rough_wood | torch dec06 stick, chandelier dec27 posts |
| rag | hessian_380 | torch head wrap |
| bark | bark_brown_02 | campfire dec24 logs |
| staves | brown_planks_03 | buoy barrel |
| ember | marble_rock_01 through a fire ramp | ember beds (campfire, torch head, lantern oil) |

Procedural (numpy, this folder's own work): candleglow (the shared CC0 Flame03 frames re-centred with a
glow blurred from each frame), sparks (rising spark flipbook), rope (buoy bands), logend (cut log ends), orb (Plane of Air orb clouds,
seamless around the sphere), halo (soft radial glow card), seaweed (dec58 frond atlas), coral (dec59 coral and
tendril atlas). Usage: make_textures.py [set ...]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / 'source' / 'polyhaven'
OUT = HERE / 'textures'
LUMA = np.array([0.2126, 0.7152, 0.0722])


def linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


# ------------------------------------------------------------------ Poly Haven derived sets
def load(asset, kind, size):
    image = Image.open(SOURCE / asset / f'{asset}_{kind}_1k.png')
    if kind == 'rough':
        values = np.asarray(image).astype(np.float64)
        values = values / 257.0 if image.mode.startswith('I') else values
        if values.ndim == 3:
            values = values[..., 0]
        image = Image.fromarray(values.astype(np.float32), 'F')
        if image.size != (size, size):
            image = image.resize((size, size), Image.BILINEAR)
        return np.asarray(image).astype(np.float64)
    image = image.convert('RGB')
    if image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    return np.asarray(image).astype(np.float64)


def graded(asset, size, saturation, hue, mean, contrast=1.0, ramp=None, invert=False, flatten=0.0):
    lin = linear(load(asset, 'diff', size))
    lum = lin @ LUMA
    if ramp is not None:
        lo, hi = np.percentile(lum, 1), np.percentile(lum, 99)
        t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)
        t = 1 - t if invert else t
        return np.stack([np.interp(t, [p for p, _ in ramp], [linear(c[i]) for _, c in ramp]) for i in range(3)], -1)
    if flatten:
        # Pull outlying luminance (rust spots) toward the median before grading.
        med = np.median(lum)
        lum2 = med + (lum - med) * (1 - flatten)
        lin = lin * (lum2 / np.maximum(lum, 1e-6))[..., None]
        lum = lum2
    chroma = lin - lum[..., None]
    lin = lum[..., None] + chroma * saturation
    if hue is not None:
        h = linear(hue)
        lin = (lin @ LUMA)[..., None] * (h / max(float(h @ LUMA), 1e-6))[None, None]
    if contrast != 1.0:
        m = float((lin @ LUMA).mean())
        lin = m * (np.maximum(lin, 1e-6) / m) ** contrast
    lin *= mean / max(float((lin @ LUMA).mean()), 1e-6)
    return np.clip(lin, 0, 1)


def scan_normal(asset, size, strength):
    n = load(asset, 'nor_gl', size) / 255.0 * 2 - 1
    n[..., :2] *= strength
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def scan_rough(asset, size, scale, offset, low, high):
    return np.clip(load(asset, 'rough', size) / 255.0 * scale + offset, low, high)


def save(name, colour, normal=None, rough=None, metal=0.0, alpha=None, mr_size=None):
    OUT.mkdir(parents=True, exist_ok=True)
    rgb = (srgb(colour) * 255 + 0.5).astype(np.uint8)
    if alpha is not None:
        rgba = np.dstack([rgb, (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}_basecolor.png', optimize=True)
    else:
        Image.fromarray(rgb).save(OUT / f'{name}_basecolor.png', optimize=True)
    if normal is not None:
        Image.fromarray((normal * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_normal.png', optimize=True)
    if rough is not None:
        metal_map = metal if np.ndim(metal) else np.full(rough.shape, metal)
        mr = np.dstack([np.zeros(rough.shape), rough, metal_map])
        image = Image.fromarray((mr * 255 + 0.5).astype(np.uint8))
        if mr_size and mr_size != image.width:
            image = image.resize((mr_size, mr_size * image.height // image.width), Image.LANCZOS)
        image.save(OUT / f'{name}_mr.png', optimize=True)
    weights = alpha if alpha is not None else np.ones(colour.shape[:2])
    mask = weights > min(0.5, float(weights.max()) * 0.5)
    return [round(float(v), 5) for v in colour[mask].mean(0)]


def derive(name, asset, size=512, saturation=0.3, hue=None, mean=0.2, contrast=1.0, ramp=None, invert=False,
           flatten=0.0, normal_strength=1.0, rough=(1.0, 0.0), rough_range=(0.25, 1.0), metal=0.2, mr_size=256):
    colour = graded(asset, size, saturation, hue, mean, contrast, ramp, invert, flatten)
    return save(name, colour, scan_normal(asset, size, normal_strength),
                scan_rough(asset, size, rough[0], rough[1], *rough_range), metal, mr_size=mr_size)


EMBER_RAMP = [(0.0, (70, 12, 4)), (0.35, (165, 50, 12)), (0.65, (225, 105, 28)), (0.9, (250, 170, 60)),
              (1.0, (255, 215, 120))]
PBR = {
    'iron_dark': dict(asset='rusty_metal_04', saturation=0.2, hue=(120, 104, 98), mean=0.2, contrast=1.15,
                      rough=(0.8, 0.0), rough_range=(0.28, 0.8), metal=0.3, normal_strength=2.5, size=256),
    'iron_grey': dict(asset='rusty_metal_02', saturation=0.0, hue=(120, 120, 124), mean=0.4, contrast=0.8,
                      flatten=0.6, rough=(0.5, 0.05), rough_range=(0.22, 0.55), metal=0.35, normal_strength=1.5,
                      size=256),
    'iron_smooth': dict(asset='blue_metal_plate', saturation=0.0, hue=(116, 106, 100), mean=0.2, contrast=1.2,
                        rough=(0.6, 0.05), rough_range=(0.22, 0.5), metal=0.35, normal_strength=1.0, size=256),
    'copper': dict(asset='blue_metal_plate', saturation=0.0, hue=(205, 125, 70), mean=0.42, contrast=1.6,
                   rough=(0.7, 0.05), rough_range=(0.22, 0.6), metal=0.35, normal_strength=1.2, size=256),
    'brass': dict(asset='blue_metal_plate', saturation=0.0, hue=(225, 175, 120), mean=0.5, contrast=1.4,
                  rough=(0.6, 0.05), rough_range=(0.18, 0.5), metal=0.4, normal_strength=1.0, size=256),
    'wax': dict(asset='leather_white', saturation=0.0, hue=(246, 238, 222), mean=0.86, contrast=3.0,
                rough=(0.5, 0.2), rough_range=(0.3, 0.6), metal=0.0, normal_strength=2.0, size=256),
    'wood': dict(asset='rough_wood', saturation=0.35, hue=(180, 112, 62), mean=0.3, contrast=1.4,
                 rough=(0.6, 0.35), rough_range=(0.55, 0.95), metal=0.0, normal_strength=1.5, size=512),
    'rag': dict(asset='hessian_380', saturation=0.4, hue=(170, 105, 60), mean=0.3, contrast=1.6,
                rough=(0.5, 0.45), rough_range=(0.6, 0.98), metal=0.0, normal_strength=2.0, size=256),
    'bark': dict(asset='bark_brown_02', saturation=0.15, hue=(140, 96, 64), mean=0.25, contrast=1.3,
                 rough=(0.5, 0.45), rough_range=(0.6, 0.98), metal=0.0, normal_strength=1.4, size=512),
    'staves': dict(asset='brown_planks_03', saturation=0.3, hue=(190, 118, 68), mean=0.33, contrast=1.3,
                   rough=(0.6, 0.3), rough_range=(0.45, 0.9), metal=0.0, normal_strength=1.5, size=512),
    'ember': dict(asset='marble_rock_01', ramp=EMBER_RAMP, invert=True, rough=(0.3, 0.6), rough_range=(0.6, 0.95),
                  metal=0.0, normal_strength=1.4, size=256),
}


# ------------------------------------------------------------------ procedural helpers
def noise(shape, power, seed):
    """Tileable fractal noise (FFT-filtered white noise), normalised to 0..1."""
    rng = np.random.default_rng(seed)
    white = rng.normal(size=shape)
    fy = np.fft.fftfreq(shape[0])[:, None] * shape[0]
    fx = np.fft.fftfreq(shape[1])[None, :] * shape[1]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    field = np.real(np.fft.ifft2(np.fft.fft2(white) / f ** power))
    field -= field.min()
    return field / field.max()


def height_normal(height, strength):
    gy, gx = np.gradient(height)
    n = np.dstack([-gx * strength, gy * strength, np.ones(height.shape)])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def ramp_colour(t, stops):
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, [p for p, _ in stops], [linear(c[i]) for _, c in stops]) for i in range(3)], -1)


def rope():
    """Braided rope bands (buoy): u around the band (8 strand twists per repeat), v across it."""
    w, h = 256, 64
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    phase = (x / w * 8 + y / h * 1.0) % 1.0
    strand = np.sin(np.pi * phase) ** 0.6
    across = np.sin(np.pi * (y + 0.5) / h) ** 0.4
    fibre = noise((h, w), 1.2, 21)
    hgt = strand * across * (0.85 + 0.15 * fibre)
    colour = ramp_colour(hgt, [(0, (20, 14, 9)), (0.6, (70, 52, 34)), (1, (120, 92, 60))])
    rough = 0.7 + 0.25 * (1 - hgt)
    return save('rope', colour, height_normal(hgt * 6, 1.0), rough, 0.0)


def logend():
    """Cut log end: reddish sapwood with growth rings and radial cracks inside a dark bark rim (disc UV 0..1)."""
    n = 256
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / n * 2 - 1
    r = np.hypot(x, y)
    a = np.arctan2(y, x)
    wobble = 0.03 * noise((n, n), 2.2, 5)
    rings = 0.5 + 0.5 * np.cos((r + wobble) * 2 * np.pi * 9)
    cracks = np.clip(1 - np.abs(np.sin(a * 5 + 3 * r)) * 30 * (1.2 - r), 0, 1) * (r > 0.15) * 0.8
    grain = noise((n, n), 1.0, 6)
    t = 0.55 + 0.25 * rings + 0.15 * (grain - 0.5) - 0.6 * cracks
    t = np.where(r > 0.86, 0.12 + 0.1 * grain, t)
    t = np.where(r < 0.05, 0.4, t)
    colour = ramp_colour(t, [(0, (25, 14, 9)), (0.35, (110, 45, 28)), (0.7, (190, 92, 58)), (1, (225, 140, 95))])
    hgt = rings * 0.3 - cracks + (r > 0.86) * 0.8
    return save('logend', colour, height_normal(hgt, 3.0), 0.8 + 0.15 * (1 - rings), 0.0)


def orb():
    """Silver clouds inside the Plane of Air orb: equirectangular (u around, seamless; v pole to pole), swirled
    fractal noise through the native sprite's luminance ramp (dark grey 56 to white 249)."""
    w, h = 512, 256
    base = noise((h, w), 1.6, 31)
    warp_x = noise((h, w), 2.2, 32) - 0.5
    warp_y = noise((h, w), 2.2, 33) - 0.5
    yy, xx = np.mgrid[0:h, 0:w]
    sx = (xx + warp_x * 90).astype(int) % w
    sy = np.clip(yy + warp_y * 45, 0, h - 1).astype(int)
    swirled = base[sy, sx]
    detail = noise((h, w), 1.1, 34)
    t = np.clip((swirled - 0.3) * 2.1 + 0.25 * (detail - 0.5), 0, 1)
    t = t * t * (3 - 2 * t)                      # sharper cloud edges, dark streaks between them
    colour = ramp_colour(t, [(0, (40, 39, 38)), (0.25, (90, 87, 82)), (0.5, (140, 137, 128)), (0.75, (196, 192, 180)),
                             (1, (252, 250, 240))])
    rough = 0.12 + 0.1 * (1 - t)
    return save('orb', colour, height_normal(t, 1.5), rough, 0.0)


def halo():
    """Soft radial glow for camera-facing halo cards (white; COLOR_0 colours it): alpha falls off from the centre."""
    n = 128
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / n * 2 - 1
    r = np.hypot(x, y)
    alpha = np.clip(1 - r, 0, 1) ** 1.4      # soft additive glow (lantern, torch and campfire halos)
    colour = np.ones((n, n, 3))
    save('halo', colour, alpha=alpha)
    return [1.0, 1.0, 1.0]


# ------------------------------------------------------------------ underwater plants
def stroke(img, alp, hgt, points, radius, colour, hgt_value=1.0):
    """Draw a soft-edged polyline (points in pixels) of the given radius (pixels, scalar or per point)."""
    h, w = alp.shape
    points = np.asarray(points, np.float64)
    radius = np.broadcast_to(np.asarray(radius, np.float64), (len(points),))
    for (p0, p1), (r0, r1) in zip(zip(points, points[1:]), zip(radius, radius[1:])):
        lo = np.floor(np.minimum(p0, p1) - max(r0, r1) - 2).astype(int)
        hi = np.ceil(np.maximum(p0, p1) + max(r0, r1) + 2).astype(int)
        lo = np.maximum(lo, 0)
        hi = np.minimum(hi, [w - 1, h - 1])
        if (hi < lo).any():
            continue
        yy, xx = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1].astype(np.float64)
        d = p1 - p0
        length2 = max(float(d @ d), 1e-9)
        t = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / length2, 0, 1)
        dist = np.hypot(xx - (p0[0] + t * d[0]), yy - (p0[1] + t * d[1]))
        r = r0 + (r1 - r0) * t
        cover = np.clip(r + 0.5 - dist, 0, 1)
        dome = np.sqrt(np.clip(1 - (dist / np.maximum(r, 0.5)) ** 2, 0, 1)) * hgt_value
        sl = (slice(lo[1], hi[1] + 1), slice(lo[0], hi[0] + 1))
        new = cover > alp[sl] * 0.999
        take = cover > 0
        img[sl][take & new] = np.asarray(colour)[None] if np.ndim(colour) == 1 else colour
        hgt[sl] = np.where(take, np.maximum(hgt[sl], dome * cover), hgt[sl])
        alp[sl] = np.maximum(alp[sl], cover)


def frond_row(img, alp, hgt, y0, rows, rng, variant):
    """One seaweed frond lying along u (base at the left, tip at the right) in rows y0..y0+rows: an olive stalk, then
    a pinnate blade of serrated leaflets on a reddish-brown midrib, widest at about 40 % and tapering to the tip, in
    the native weed's yellow-greens (median sRGB 95, 115, 21; dark 36, 47, 2; light 119, 151, 26)."""
    w = img.shape[1]
    cy = y0 + rows / 2
    stalk_end = int(w * (0.19 + 0.025 * variant))
    bend = rng.uniform(-0.05, 0.05) * rows
    rib = [(x, cy + bend * np.sin(np.pi * x / w) + 0.04 * rows * np.sin(x / w * 7 + variant)) for x in
           np.linspace(0, w - 6, 60)]
    rib = np.array(rib)
    stalk_colour = linear((96, 104, 30))
    stroke(img, alp, hgt, rib[rib[:, 0] <= stalk_end + 20], np.linspace(rows * 0.05, rows * 0.03,
                                                                       len(rib[rib[:, 0] <= stalk_end + 20])),
           stalk_colour, 0.8)
    darks = [linear(c) for c in ((40, 55, 4), (58, 78, 8), (72, 92, 12))]
    lights = [linear(c) for c in ((96, 118, 20), (112, 140, 26), (128, 160, 34), (104, 126, 16))]
    leaflets = int(230 + 30 * variant)
    for k in range(leaflets):
        s = rng.uniform(0, 1)
        x = stalk_end + s * (w - 12 - stalk_end)
        t = (x - stalk_end) / (w - stalk_end)
        envelope = np.sin(np.pi * min(0.97, t) ** 0.85) * (1 - 0.15 * t)
        length = rows * 0.47 * envelope * rng.uniform(0.7, 1.05)
        if length < 3:
            continue
        side = 1 if k % 2 else -1
        ry = np.interp(x, rib[:, 0], rib[:, 1])
        angle = np.radians(rng.uniform(22, 40))          # leaflets point toward the tip
        tip = (x + length * np.cos(angle), ry + side * length * np.sin(angle))
        mid = (x + length * 0.5 * np.cos(angle) - 2, ry + side * length * 0.55 * np.sin(angle))
        shade = rng.uniform()
        colour = lights[rng.integers(len(lights))] if shade > 0.35 else darks[rng.integers(len(darks))]
        width = max(1.4, rows * 0.022 * rng.uniform(0.7, 1.2))
        bow = side * length * 0.12
        mid = (mid[0] + 2, mid[1] - bow * 0.3)
        stroke(img, alp, hgt, [(x, ry), mid, tip], [width * 0.8, width, 0.5], colour, 0.6 + 0.4 * shade)
    rib_colour = linear((92, 60, 20))
    leafy = rib[(rib[:, 0] > stalk_end - 10) & (rib[:, 0] < w * 0.96)]
    stroke(img, alp, hgt, leafy, np.linspace(rows * 0.016, 0.8, len(leafy)), rib_colour, 1.0)


def write_profile(name, alpha, bands, bins=48):
    """Per atlas band (top, height in pixels) and per u bin, the covered rows (alpha > 0.2) as fractions of the
    band, top = 0: textures/<name>_profile.json, read by build_weed.py to fit the strips to the painted shapes."""
    w = alpha.shape[1]
    out = []
    for top, height in bands:
        band = alpha[top:top + height] > 0.2
        rows = []
        for b in range(bins):
            cols = band[:, b * w // bins:(b + 1) * w // bins].any(1)
            ys = np.nonzero(cols)[0]
            rows.append([float(ys.min()) / height, float(ys.max() + 1) / height] if len(ys) else [0.5, 0.5])
        out.append({'top': top / alpha.shape[0], 'height': height / alpha.shape[0], 'bins': rows})
    (OUT / f'{name}_profile.json').write_text(json.dumps(out, indent=0))


def seaweed():
    """dec58 frond atlas: four frond variants, each a 1024 x 256 row (length along u, base at u = 0)."""
    w, rows = 1024, 256
    img = np.zeros((rows * 4, w, 3))
    alp = np.zeros((rows * 4, w))
    hgt = np.zeros((rows * 4, w))
    rng = np.random.default_rng(58)
    for v in range(4):
        frond_row(img, alp, hgt, v * rows, rows, rng, v)
    grain = noise(alp.shape, 1.0, 59)
    img *= (0.85 + 0.3 * grain)[..., None]
    rough = 0.55 + 0.3 * (1 - hgt)
    alpha = np.clip((alp - 0.35) * 3, 0, 1)
    write_profile('seaweed', alpha, [(v * rows, rows) for v in range(4)])
    return save('seaweed', np.clip(img, 0, 1), height_normal(hgt * 3, 1.0), rough, 0.0, alpha=alpha, mr_size=512)


def coral_envelope(t):
    """Half width of the coral spire (fraction of the row) at t along its length: narrow stem, widest at about 40 %,
    tapering to the tip, as the native weed02 sprite."""
    return 0.47 * np.sin(np.pi * min(1.0, 0.12 + t * 1.05) ** 0.8) * (1 - 0.35 * t)


def branch(img, alp, hgt, rng, start, angle, length, radius, depth, colours, cy, rows):
    """Recursive coral branch (pixels; angle 0 = along +u, toward the tip): it bends back toward its own direction,
    stops at the spire envelope and forks forward."""
    w = img.shape[1]
    points = [np.array(start, np.float64)]
    a = angle
    steps = max(3, int(length / 6))
    for _ in range(steps):
        a += rng.normal(0, 0.18) + 0.25 * (angle - a)
        p = points[-1] + length / steps * np.array([np.cos(a), np.sin(a)])
        if p[0] >= w - 6 or abs(p[1] - cy) > coral_envelope(p[0] / w) * rows:
            break
        points.append(p)
    if len(points) < 2:
        return
    tone = colours[min(depth, len(colours) - 1)]
    stroke(img, alp, hgt, points, np.linspace(radius, radius * 0.75, len(points)), tone, 1.0)
    stroke(img, alp, hgt, [points[-1], points[-1] + 0.1], radius * 1.05, colours[-1], 1.0)   # polyp tip
    if depth >= 3:
        return
    for k in range(rng.integers(2, 5)):
        i = rng.integers(1, len(points))
        side = 1 if (k + depth) % 2 else -1
        branch(img, alp, hgt, rng, points[i], a + side * rng.uniform(0.4, 0.9), length * rng.uniform(0.4, 0.65),
               max(1.3, radius * 0.7), depth + 1, colours, cy, rows)


def tendril(img, alp, hgt, rng, y0, rows, colours):
    """A thin wavy green strand along u (native green median 83, 110, 14)."""
    w = img.shape[1]
    xs = np.linspace(2, w - 4, 90)
    amp = rows * 0.18
    ys = y0 + rows / 2 + amp * np.sin(xs / w * rng.uniform(10, 15) + rng.uniform(0, 6)) * (0.3 + 0.7 * xs / w)
    radius = np.linspace(rows * 0.11, rows * 0.05, len(xs))
    stroke(img, alp, hgt, np.stack([xs, ys], -1), radius, colours[0], 1.0)
    # a lighter rim on the upper side (painted light from above)
    stroke(img, alp, hgt, np.stack([xs, ys - radius * 0.35], -1), radius * 0.45, colours[1], 1.0)
    # a few short side shoots
    for _ in range(4):
        i = rng.integers(10, len(xs) - 10)
        a = rng.choice([-1, 1]) * rng.uniform(0.4, 0.8)
        p0 = np.array([xs[i], ys[i]])
        p1 = p0 + rows * 0.3 * np.array([np.cos(a), np.sin(a)])
        p1[1] = np.clip(p1[1], y0 + 3, y0 + rows - 3)
        stroke(img, alp, hgt, [p0, p1], [radius[i] * 0.7, 1.0], colours[0], 0.8)


def coral():
    """dec59 atlas, 1024 x 1024, everything lying along u (base at u = 0): rows 0-255 and 256-511 two red branching
    coral fans (native red median 69, 22, 3; dark 18, 5, 0; light 136, 47, 9; orange tips), rows 512-1023 four
    128-high green tendrils."""
    w = 1024
    img = np.zeros((w, w, 3))
    alp = np.zeros((w, w))
    hgt = np.zeros((w, w))
    rng = np.random.default_rng(59)
    reds = [linear(c) for c in ((60, 14, 4), (92, 26, 6), (118, 38, 8), (140, 50, 10), (176, 76, 20))]
    for v in range(2):
        cy, rows = v * 256 + 128, 256
        stem = np.array([(x, cy + 6 * np.sin(x / 140 + v)) for x in np.linspace(2, 850, 80)])
        stroke(img, alp, hgt, stem, np.linspace(9, 2.5, len(stem)), reds[0], 1.0)
        for k in range(46):
            t = (k + rng.uniform(0, 0.8)) / 46
            x0 = 30 + t * 930
            side = 1 if k % 2 else -1
            angle = side * rng.uniform(0.5, 1.0)
            reach = coral_envelope(t) * rows / max(np.sin(abs(angle)), 0.3)
            branch(img, alp, hgt, rng, (x0, cy + 6 * np.sin(x0 / 140 + v)), angle, reach * rng.uniform(0.8, 1.3),
                   6.5 - 3 * t, 1, reds, cy, rows)
    greens = [linear((78, 104, 12)), linear((112, 142, 28))]
    for k in range(4):
        tendril(img, alp, hgt, rng, 512 + k * 128, 128, greens)
    grain = noise(alp.shape, 1.0, 60)
    img *= (0.85 + 0.3 * grain)[..., None]
    rough = 0.45 + 0.35 * (1 - hgt)
    alpha = np.clip((alp - 0.35) * 3, 0, 1)
    write_profile('coral', alpha, [(0, 256), (256, 256)] + [(512 + k * 128, 128) for k in range(4)])
    return save('coral', np.clip(img, 0, 1), height_normal(hgt * 4, 1.0), rough, 0.0, alpha=alpha, mr_size=512)


def orbhalo():
    """Halo of the Plane of Air orb: a card 1.3 x the sphere radius, so the sphere's silhouette is at r = 0.77; the
    glow is 0.5 opaque there and fades to nothing at the card edge (inside, the sphere hides it)."""
    n = 128
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / n * 2 - 1
    r = np.hypot(x, y)
    alpha = 0.5 * np.clip((1 - r) / 0.23, 0, 1) ** 1.6
    save('orbhalo', np.ones((n, n, 3)), alpha=alpha)
    return [1.0, 1.0, 1.0]


FLAMES = HERE.parents[1] / 'mm6_dungeons_3d' / 'textures'


def candleglow():
    """Additive candle flame with its own halo: the shared Flame03 flipbook (CC0 Unity Labs, 16 x 4 frames of
    64 x 128, ../../mm6_dungeons_3d/textures/FLAMES.md) re-centred in 128 x 128 frames (2048 x 512), each frame's
    flame plus a soft warm glow blurred from that frame's own alpha, so the halo breathes with the flame. Drawn
    additive (openyamm_additive): colour times alpha is what each texel adds. The flame spans 0.35-0.70 of a frame's
    width; its base and tips keep Flame03's heights (texture v 0.055 and 0.70 from the frame bottom)."""
    from scipy.ndimage import gaussian_filter
    src = Image.open(FLAMES / 'flame03_basecolor.png').convert('RGBA')
    flame = np.asarray(src).astype(np.float64) / 255.0
    fw, fh = 64, 128
    out_rgb = np.zeros((fh * 4, 128 * 16, 3))
    out_a = np.zeros((fh * 4, 128 * 16))
    glow_colour = linear((255, 120, 36))
    edge = np.minimum.outer(np.minimum(np.arange(fh), np.arange(fh)[::-1]),
                            np.minimum(np.arange(128), np.arange(128)[::-1]))
    window = np.clip(edge / 10.0, 0, 1) ** 1.5
    blurs = []
    for row in range(4):
        for col in range(16):
            a = np.zeros((fh, 128))
            a[:, 32:96] = flame[row * fh:(row + 1) * fh, col * fw:(col + 1) * fw, 3]
            blurs.append(gaussian_filter(a, 15.0))
    peak = max(b.max() for b in blurs)
    for row in range(4):
        for col in range(16):
            cell = flame[row * fh:(row + 1) * fh, col * fw:(col + 1) * fw]
            a = np.zeros((fh, 128))
            rgb = np.zeros((fh, 128, 3))
            a[:, 32:96] = cell[..., 3]
            rgb[:, 32:96] = linear(cell[..., :3] * 255.0)
            g = 0.95 * blurs[row * 16 + col] / peak * window
            premult = rgb * a[..., None] + glow_colour[None, None] * g[..., None]
            alpha = np.clip(a + g, 0, 1)
            colour = np.clip(premult / np.maximum(alpha, 1e-4)[..., None], 0, 1)
            out_rgb[row * fh:(row + 1) * fh, col * 128:(col + 1) * 128] = colour
            out_a[row * fh:(row + 1) * fh, col * 128:(col + 1) * 128] = alpha
    save('candleglow', out_rgb, alpha=out_a)
    return [1.0, 1.0, 1.0]


def sparks():
    """Rising sparks for the fires (additive, camera-facing): 8 x 4 frames of 128 x 256 (1024 x 1024), a seamless
    32-frame loop (every spark repeats a whole number of times per loop). Hot yellow-white sparks leave the bottom
    third, drift and flutter upward and cool to orange-red as they fade. Own procedural work."""
    rng = np.random.default_rng(24)
    w, h, cols, rows = 128, 256, 8, 4
    frames = cols * rows
    out = np.zeros((h * rows, w * cols, 3))
    alpha = np.zeros((h * rows, w * cols))
    count = 24
    x0 = rng.normal(0.5, 0.12, count).clip(0.2, 0.8)
    y0 = rng.uniform(0.62, 0.86, count)
    rise = rng.uniform(0.35, 0.75, count)
    cycles = rng.integers(1, 3, count)
    phase = rng.uniform(0, 1, count)
    sway = rng.uniform(0.02, 0.08, count)
    wobble = rng.uniform(4, 9, count)
    size = rng.uniform(1.0, 2.2, count)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    hot, warm, cool = linear((255, 236, 170)), linear((255, 150, 50)), linear((220, 70, 20))
    for f in range(frames):
        canvas = np.zeros((h, w, 3))
        cover = np.zeros((h, w))
        for i in range(count):
            s = (f / frames * cycles[i] + phase[i]) % 1.0
            if s < 0.03:
                continue
            x = (x0[i] + sway[i] * np.sin(s * wobble[i] + i)) * w
            y = (y0[i] - rise[i] * s) * h
            bright = (1 - s) ** 1.4 * min(1.0, (s - 0.03) * 12)
            r = size[i] * (1.0 - 0.4 * s)
            d2 = (xx - x) ** 2 + (yy - y) ** 2
            dot = np.exp(-d2 / (2 * r * r)) * bright
            tone = hot * (1 - s) + warm * s if s < 0.5 else warm * (1 - s) * 2 + cool * (2 * s - 1)
            canvas += dot[..., None] * tone[None, None]
            cover = np.maximum(cover, dot)
        r0, c0 = (f // cols) * h, (f % cols) * w
        out[r0:r0 + h, c0:c0 + w] = np.clip(canvas / np.maximum(cover, 1e-4)[..., None], 0, 1)
        alpha[r0:r0 + h, c0:c0 + w] = np.clip(cover * 1.6, 0, 1)
    save('sparks', out, alpha=alpha)
    return [1.0, 1.0, 1.0]


PROCEDURAL = {'candleglow': candleglow, 'sparks': sparks, 'orbhalo': orbhalo, 'rope': rope, 'logend': logend, 'orb': orb, 'halo': halo, 'seaweed': seaweed, 'coral': coral}


def main():
    names = sys.argv[1:] or list(PBR) + list(PROCEDURAL)
    path = OUT / 'means.json'
    means = json.loads(path.read_text()) if path.exists() else {}
    for name in names:
        means[name] = derive(name, **PBR[name]) if name in PBR else PROCEDURAL[name]()
        print('TEXTURE', name, means[name], 'sRGB', [round(float(v) * 255) for v in srgb(np.array(means[name]))])
    path.write_text(json.dumps(means, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
